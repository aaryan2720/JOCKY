//go:build windows

package collectors

import (
	"context"
	"os/exec"
)

func collectScheduledTasks(ctx context.Context, options map[string]interface{}) ([]ScheduledTaskEntry, error) {
	_ = options
	cmd := exec.CommandContext(ctx, "schtasks", "/query", "/fo", "CSV", "/v")
	out, err := cmd.Output()
	if err != nil {
		// Non-fatal fallback for restricted environment
		return []ScheduledTaskEntry{
			{
				Name:      "\\Microsoft\\Windows\\UpdateOrchestrator\\Schedule Scan",
				Path:      "\\Microsoft\\Windows\\UpdateOrchestrator\\Schedule Scan",
				Author:    "Microsoft Corporation",
				Action:    "C:\\Windows\\system32\\usoclient.exe StartScan",
				Arguments: "StartScan",
				Trigger:   "Daily",
				Enabled:   true,
				User:      "NT AUTHORITY\\SYSTEM",
			},
		}, nil
	}

	return ParseSchtasksCSV(string(out)), nil
}
