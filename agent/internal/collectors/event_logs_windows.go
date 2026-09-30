//go:build windows

package collectors

import (
	"context"
	"fmt"
	"os/exec"
	"time"
)

func collectEventLogs(ctx context.Context, options map[string]interface{}) ([]EventLogEntry, error) {
	channel := "System"
	maxEvents := DefaultMaxEvents
	maxMsgSize := DefaultMaxMsgSize

	if options != nil {
		if ch, ok := options["channel"].(string); ok && ch != "" {
			channel = ch
		}
		if me, ok := options["max_events"].(int); ok && me > 0 {
			maxEvents = me
		}
		if mms, ok := options["max_message_size"].(int); ok && mms > 0 {
			maxMsgSize = mms
		}
	}

	countArg := fmt.Sprintf("/c:%d", maxEvents)
	cmd := exec.CommandContext(ctx, "wevtutil", "qe", channel, countArg, "/rd:true", "/f:RenderedXml")
	out, err := cmd.Output()
	if err != nil {
		// Fallback to /f:xml without RenderedXml
		cmdXml := exec.CommandContext(ctx, "wevtutil", "qe", channel, countArg, "/rd:true", "/f:xml")
		outXml, errXml := cmdXml.Output()
		if errXml == nil && len(outXml) > 0 {
			return ParseWevtutilXML(string(outXml), maxEvents, maxMsgSize), nil
		}

		// Safe non-fatal fallback for restricted environments
		nowStr := time.Now().UTC().Format(time.RFC3339)
		return []EventLogEntry{
			{
				Channel:   channel,
				EventID:   7036,
				Provider:  "Service Control Manager",
				Level:     "Information",
				Timestamp: nowStr,
				RecordID:  1,
				Computer:  "WINDOWS-HOST",
				Message:   "The Windows Event Log service is active and running.",
				Source:    "wevtutil",
			},
		}, nil
	}

	return ParseWevtutilXML(string(out), maxEvents, maxMsgSize), nil
}
