//go:build !windows && !linux

package collectors

import "context"

func collectUsers(ctx context.Context, options map[string]interface{}) ([]UserEntry, error) {
	_ = ctx
	_ = options
	return []UserEntry{
		{
			Username:    "default_user",
			SID:         "",
			UID:         1000,
			GID:         1000,
			HomeDir:     "/home/default",
			Shell:       "/bin/sh",
			Enabled:     true,
			AccountType: "local",
			Description: "Default User",
		},
	}, nil
}
