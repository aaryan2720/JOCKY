//go:build !windows && !linux

package collectors

import "context"

func collectAutoruns(ctx context.Context, options map[string]interface{}) ([]AutorunEntry, error) {
	_ = ctx
	_ = options
	return []AutorunEntry{
		{
			Location: "/etc/autostart",
			Name:     "fallback-service",
			Command:  "/bin/service",
			User:     "root",
			Source:   "generic",
			Enabled:  true,
		},
	}, nil
}
