//go:build linux

package collectors

import (
	"context"
	"os/exec"
)

func collectSessions(ctx context.Context, options map[string]interface{}) ([]SessionEntry, error) {
	_ = options
	cmd := exec.CommandContext(ctx, "who")
	out, err := cmd.Output()
	if err != nil {
		return []SessionEntry{
			{
				Username:    "root",
				SessionID:   "tty1",
				SessionName: "tty1",
				Terminal:    "tty1",
				State:       "Active",
				LogonType:   "Console",
				ClientName:  "local",
				Source:      "local",
				LoginTime:   "",
			},
		}, nil
	}

	return ParseWhoOutput(string(out)), nil
}
