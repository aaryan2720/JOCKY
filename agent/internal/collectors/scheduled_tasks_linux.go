//go:build linux

package collectors

import (
	"context"
	"os"
	"path/filepath"
)

func collectScheduledTasks(ctx context.Context, options map[string]interface{}) ([]ScheduledTaskEntry, error) {
	_ = options
	var entries []ScheduledTaskEntry

	// 1. /etc/crontab
	if data, err := os.ReadFile("/etc/crontab"); err == nil {
		entries = append(entries, ParseCrontab(string(data), "/etc/crontab")...)
	}

	// 2. /etc/cron.d/
	if files, err := os.ReadDir("/etc/cron.d"); err == nil {
		for _, file := range files {
			if ctx.Err() != nil {
				return entries, ctx.Err()
			}
			if file.IsDir() || file.Name() == ".placeholder" {
				continue
			}
			path := filepath.Join("/etc/cron.d", file.Name())
			if data, err := os.ReadFile(path); err == nil {
				entries = append(entries, ParseCrontab(string(data), path)...)
			}
		}
	}

	// 3. User crontabs in /var/spool/cron/crontabs
	spoolDirs := []string{"/var/spool/cron/crontabs", "/var/spool/cron"}
	for _, sdir := range spoolDirs {
		if files, err := os.ReadDir(sdir); err == nil {
			for _, file := range files {
				if file.IsDir() {
					continue
				}
				path := filepath.Join(sdir, file.Name())
				if data, err := os.ReadFile(path); err == nil {
					entries = append(entries, ParseCrontab(string(data), path)...)
				}
			}
		}
	}

	return entries, nil
}
