//go:build !windows && !linux

package collectors

import "context"

func collectScheduledTasks(ctx context.Context, options map[string]interface{}) ([]ScheduledTaskEntry, error) {
	_ = ctx
	_ = options
	return []ScheduledTaskEntry{
		{
			Name:      "generic-cron",
			Path:      "/etc/crontab",
			Author:    "root",
			Action:    "/bin/check",
			Arguments: "",
			Trigger:   "0 * * * *",
			Enabled:   true,
			User:      "root",
		},
	}, nil
}
