package collectors

import (
	"context"
	"strconv"
	"strings"
	"time"
)

// ProcessEntry represents a normalized process artifact.
type ProcessEntry struct {
	PID             int    `json:"pid"`
	PPID            int    `json:"ppid"`
	Name            string `json:"name"`
	Path            string `json:"path"`
	CommandLine     string `json:"command_line"`
	User            string `json:"user"`
	SignatureStatus string `json:"signature_status"` // "signed", "unsigned", "unsupported"
}

// ProcessCollector collects read-only information about running processes.
type ProcessCollector struct{}

// NewProcessCollector returns a new instance of ProcessCollector.
func NewProcessCollector() *ProcessCollector {
	return &ProcessCollector{}
}

func (c *ProcessCollector) Name() string {
	return "processes"
}

// Collect queries the running processes on the host.
func (c *ProcessCollector) Collect(ctx context.Context, options map[string]interface{}) ([]Artifact, error) {
	entries, err := collectProcesses(ctx, options)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, p := range entries {
		artifacts = append(artifacts, Artifact{
			Type:        "process",
			CollectedAt: now,
			Data: map[string]interface{}{
				"pid":              p.PID,
				"ppid":             p.PPID,
				"name":             p.Name,
				"path":             p.Path,
				"command_line":     p.CommandLine,
				"user":             p.User,
				"signature_status": p.SignatureStatus,
			},
		})
	}

	return artifacts, nil
}

// ParseLinuxPsOutput parses standard Linux `ps -eo pid,ppid,user,args` output into ProcessEntry records.
func ParseLinuxPsOutput(output string) []ProcessEntry {
	lines := strings.Split(output, "\n")
	var entries []ProcessEntry

	for i, line := range lines {
		line = strings.TrimSpace(line)
		if i == 0 || line == "" {
			continue // skip header or blank
		}

		fields := strings.Fields(line)
		if len(fields) < 4 {
			continue
		}

		pid, _ := strconv.Atoi(fields[0])
		ppid, _ := strconv.Atoi(fields[1])
		user := fields[2]
		cmdline := strings.Join(fields[3:], " ")
		name := fields[3]
		// extract basename
		if slashIdx := strings.LastIndex(name, "/"); slashIdx != -1 {
			name = name[slashIdx+1:]
		}

		entries = append(entries, ProcessEntry{
			PID:             pid,
			PPID:            ppid,
			Name:            name,
			Path:            fields[3],
			CommandLine:     cmdline,
			User:            user,
			SignatureStatus: "unsupported",
		})
	}

	return entries
}

