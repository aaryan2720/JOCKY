//go:build !windows && !linux

package collectors

import "context"

func collectSessions(ctx context.Context, options map[string]interface{}) ([]SessionEntry, error) {
	_ = ctx
	_ = options
	return []SessionEntry{
		{
			Username:    "active_user",
			SessionID:   "s1",
			SessionName: "console",
			Terminal:    "console",
			State:       "Active",
			LogonType:   "Console",
			ClientName:  "local",
			Source:      "local",
			LoginTime:   "",
		},
	}, nil
}
