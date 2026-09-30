package collectors

import (
	"context"
	"strings"
	"time"
)

// AutorunEntry represents a normalized autorun/persistence artifact.
type AutorunEntry struct {
	Location string `json:"location"`
	Name     string `json:"name"`
	Command  string `json:"command"`
	User     string `json:"user"`
	Source   string `json:"source"`  // "registry", "startup_folder", "xdg_autostart", "init.d", etc.
	Enabled  bool   `json:"enabled"`
}

// AutorunCollector enumerates safe, read-only system and user persistence mechanisms.
type AutorunCollector struct{}

// NewAutorunCollector creates an instance of AutorunCollector.
func NewAutorunCollector() *AutorunCollector {
	return &AutorunCollector{}
}

func (c *AutorunCollector) Name() string {
	return "autoruns"
}

// Collect enumerates persistence mechanisms without system modification.
func (c *AutorunCollector) Collect(ctx context.Context, options map[string]interface{}) ([]Artifact, error) {
	entries, err := collectAutoruns(ctx, options)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, a := range entries {
		artifacts = append(artifacts, Artifact{
			Type:        "autorun",
			CollectedAt: now,
			Data: map[string]interface{}{
				"location": a.Location,
				"name":     a.Name,
				"command":  a.Command,
				"user":     a.User,
				"source":   a.Source,
				"enabled":  a.Enabled,
			},
		})
	}

	return artifacts, nil
}

// ParseRegQueryOutput parses standard Windows `reg query` command output for a given key.
func ParseRegQueryOutput(output string, keyPath string, user string) []AutorunEntry {
	lines := strings.Split(output, "\n")
	var entries []AutorunEntry

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "HKEY_") || strings.HasPrefix(line, "ERROR:") {
			continue
		}

		// reg query output format: <Name>    <REG_SZ|REG_EXPAND_SZ>    <Command>
		fields := strings.Fields(line)
		if len(fields) < 3 {
			continue
		}

		name := fields[0]
		typeIdx := -1
		for i, f := range fields {
			if strings.HasPrefix(f, "REG_") {
				typeIdx = i
				break
			}
		}

		if typeIdx != -1 && typeIdx+1 < len(fields) {
			command := strings.Join(fields[typeIdx+1:], " ")
			entries = append(entries, AutorunEntry{
				Location: keyPath,
				Name:     name,
				Command:  command,
				User:     user,
				Source:   "registry",
				Enabled:  true,
			})
		}
	}

	return entries
}

// ParseDesktopFile parses a freedesktop .desktop specification file content.
func ParseDesktopFile(content string, filePath string, user string) *AutorunEntry {
	lines := strings.Split(content, "\n")
	var name, execCmd, comment string
	inDesktopEntry := false

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "[Desktop Entry]" {
			inDesktopEntry = true
			continue
		}
		if strings.HasPrefix(line, "[") && line != "[Desktop Entry]" {
			inDesktopEntry = false
			continue
		}
		if !inDesktopEntry || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		k := strings.TrimSpace(parts[0])
		v := strings.TrimSpace(parts[1])

		switch strings.ToLower(k) {
		case "name":
			name = v
		case "exec":
			execCmd = v
		case "comment":
			comment = v
		}
	}

	if execCmd == "" && name == "" {
		return nil
	}
	if name == "" {
		name = filePath
	}
	_ = comment

	return &AutorunEntry{
		Location: filePath,
		Name:     name,
		Command:  execCmd,
		User:     user,
		Source:   "xdg_autostart",
		Enabled:  true,
	}
}
