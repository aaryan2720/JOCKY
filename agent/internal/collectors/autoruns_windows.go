//go:build windows

package collectors

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
)

func collectAutoruns(ctx context.Context, options map[string]interface{}) ([]AutorunEntry, error) {
	_ = options
	var entries []AutorunEntry

	// 1. Registry Run & RunOnce Keys
	registryKeys := []struct {
		keyPath string
		user    string
	}{
		{"HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", "SYSTEM"},
		{"HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce", "SYSTEM"},
		{"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", "CURRENT_USER"},
		{"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce", "CURRENT_USER"},
		{"HKLM\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Run", "SYSTEM"},
	}

	for _, target := range registryKeys {
		if ctx.Err() != nil {
			return entries, ctx.Err()
		}

		cmd := exec.CommandContext(ctx, "reg", "query", target.keyPath)
		out, err := cmd.Output()
		if err == nil {
			parsed := ParseRegQueryOutput(string(out), target.keyPath, target.user)
			entries = append(entries, parsed...)
		}
	}

	// 2. Startup Folders
	startupFolders := []struct {
		folderPath string
		user       string
	}{
		{filepath.Join(os.Getenv("ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup"), "ALL_USERS"},
		{filepath.Join(os.Getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup"), "CURRENT_USER"},
	}

	for _, sf := range startupFolders {
		if sf.folderPath == "" {
			continue
		}
		files, err := os.ReadDir(sf.folderPath)
		if err != nil {
			continue
		}

		for _, file := range files {
			if file.IsDir() || file.Name() == "desktop.ini" {
				continue
			}

			fullPath := filepath.Join(sf.folderPath, file.Name())
			entries = append(entries, AutorunEntry{
				Location: sf.folderPath,
				Name:     file.Name(),
				Command:  fullPath,
				User:     sf.user,
				Source:   "startup_folder",
				Enabled:  true,
			})
		}
	}

	return entries, nil
}
