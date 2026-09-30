//go:build linux

package collectors

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func collectServices(ctx context.Context, options map[string]interface{}) ([]ServiceEntry, error) {
	_ = options
	var entries []ServiceEntry

	// 1. Try systemctl list-units if systemd is active
	cmd := exec.CommandContext(ctx, "systemctl", "list-units", "--type=service", "--all", "--no-pager", "--no-legend")
	out, err := cmd.Output()
	if err == nil && len(out) > 0 {
		entries = append(entries, ParseSystemctlListUnits(string(out))...)
		if len(entries) > 0 {
			return entries, nil
		}
	}

	// 2. Fallback: Parse service unit files in standard systemd directories
	unitDirs := []string{"/etc/systemd/system", "/lib/systemd/system", "/usr/lib/systemd/system"}
	for _, dir := range unitDirs {
		if files, err := os.ReadDir(dir); err == nil {
			for _, file := range files {
				if ctx.Err() != nil {
					return entries, ctx.Err()
				}
				if file.IsDir() || !strings.HasSuffix(file.Name(), ".service") {
					continue
				}
				path := filepath.Join(dir, file.Name())
				if data, err := os.ReadFile(path); err == nil {
					if entry := ParseSystemdUnitFile(string(data), file.Name()); entry != nil {
						entries = append(entries, *entry)
					}
				}
			}
		}
	}

	// 3. Fallback: Scan /etc/init.d/ scripts for legacy/non-systemd systems
	if files, err := os.ReadDir("/etc/init.d"); err == nil {
		for _, file := range files {
			if ctx.Err() != nil {
				return entries, ctx.Err()
			}
			if file.IsDir() || strings.HasPrefix(file.Name(), ".") || file.Name() == "README" {
				continue
			}
			entries = append(entries, ServiceEntry{
				Name:        file.Name(),
				DisplayName: file.Name(),
				Status:      "installed",
				StartType:   "init.d",
				Path:        filepath.Join("/etc/init.d", file.Name()),
				Source:      "init.d",
			})
		}
	}

	return entries, nil
}
