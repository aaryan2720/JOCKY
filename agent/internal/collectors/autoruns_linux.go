//go:build linux

package collectors

import (
	"context"
	"os"
	"path/filepath"
)

func collectAutoruns(ctx context.Context, options map[string]interface{}) ([]AutorunEntry, error) {
	_ = options
	var entries []AutorunEntry

	homeDir, _ := os.UserHomeDir()
	autostartDirs := []struct {
		path string
		user string
	}{
		{"/etc/xdg/autostart", "root"},
		{filepath.Join(homeDir, ".config", "autostart"), "current_user"},
	}

	for _, ad := range autostartDirs {
		if ctx.Err() != nil {
			return entries, ctx.Err()
		}

		files, err := os.ReadDir(ad.path)
		if err != nil {
			continue
		}

		for _, file := range files {
			if file.IsDir() || !filepath.HasSuffix(file.Name(), ".desktop") {
				continue
			}

			fullPath := filepath.Join(ad.path, file.Name())
			data, err := os.ReadFile(fullPath)
			if err != nil {
				continue
			}

			entry := ParseDesktopFile(string(data), fullPath, ad.user)
			if entry != nil {
				entries = append(entries, *entry)
			}
		}
	}

	// Check /etc/rc.local
	if rcStat, err := os.Stat("/etc/rc.local"); err == nil && !rcStat.IsDir() {
		entries = append(entries, AutorunEntry{
			Location: "/etc/rc.local",
			Name:     "rc.local",
			Command:  "/etc/rc.local",
			User:     "root",
			Source:   "rc.local",
			Enabled:  true,
		})
	}

	return entries, nil
}
