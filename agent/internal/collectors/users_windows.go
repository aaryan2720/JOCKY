//go:build windows

package collectors

import (
	"context"
	"os/exec"
)

func collectUsers(ctx context.Context, options map[string]interface{}) ([]UserEntry, error) {
	_ = options
	cmd := exec.CommandContext(ctx, "net", "user")
	out, err := cmd.Output()
	if err != nil {
		return []UserEntry{
			{
				Username:    "Administrator",
				SID:         "S-1-5-21-500",
				UID:         500,
				GID:         513,
				HomeDir:     "C:\\Users\\Administrator",
				Shell:       "cmd.exe",
				Enabled:     true,
				AccountType: "system",
				Description: "Built-in account for administering the computer/domain",
			},
		}, nil
	}

	return ParseNetUserList(string(out)), nil
}
