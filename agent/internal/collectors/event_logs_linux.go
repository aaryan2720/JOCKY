//go:build linux

package collectors

import (
	"context"
	"fmt"
	"os"
	"os/exec"
)

func collectEventLogs(ctx context.Context, options map[string]interface{}) ([]EventLogEntry, error) {
	maxEvents := DefaultMaxEvents
	maxMsgSize := DefaultMaxMsgSize

	if options != nil {
		if me, ok := options["max_events"].(int); ok && me > 0 {
			maxEvents = me
		}
		if mms, ok := options["max_message_size"].(int); ok && mms > 0 {
			maxMsgSize = mms
		}
	}

	// 1. Try systemd journalctl with JSON output
	nArg := fmt.Sprintf("-n%d", maxEvents)
	cmd := exec.CommandContext(ctx, "journalctl", nArg, "-o", "json", "--no-pager")
	out, err := cmd.Output()
	if err == nil && len(out) > 0 {
		entries := ParseJournaldJSON(string(out), maxEvents, maxMsgSize)
		if len(entries) > 0 {
			return entries, nil
		}
	}

	// 2. Fallback: Parse common syslog files if accessible
	syslogCandidates := []struct {
		path    string
		channel string
	}{
		{"/var/log/syslog", "syslog"},
		{"/var/log/messages", "messages"},
		{"/var/log/auth.log", "auth"},
		{"/var/log/secure", "secure"},
	}

	var allEntries []EventLogEntry
	for _, sc := range syslogCandidates {
		if ctx.Err() != nil {
			return allEntries, ctx.Err()
		}
		if data, rErr := os.ReadFile(sc.path); rErr == nil && len(data) > 0 {
			entries := ParseSyslogContent(string(data), sc.channel, maxEvents, maxMsgSize)
			allEntries = append(allEntries, entries...)
			if maxEvents > 0 && len(allEntries) >= maxEvents {
				return allEntries[:maxEvents], nil
			}
		}
	}

	return allEntries, nil
}
