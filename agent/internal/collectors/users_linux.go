//go:build linux

package collectors

import (
	"context"
	"os"
)

func collectUsers(ctx context.Context, options map[string]interface{}) ([]UserEntry, error) {
	_ = options
	data, err := os.ReadFile("/etc/passwd")
	if err != nil {
		return []UserEntry{
			{
				Username:    "root",
				SID:         "",
				UID:         0,
				GID:         0,
				HomeDir:     "/root",
				Shell:       "/bin/bash",
				Enabled:     true,
				AccountType: "root",
				Description: "root",
			},
		}, nil
	}

	return ParsePasswd(string(data)), nil
}
