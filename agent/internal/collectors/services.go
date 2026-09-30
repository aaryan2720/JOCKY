package collectors

import (
	"context"
	"strings"
	"time"
)

// ServiceEntry represents a normalized forensic service artifact.
type ServiceEntry struct {
	Name        string `json:"name"`
	DisplayName string `json:"display_name"`
	Status      string `json:"status"`       // "running", "stopped", "active", "inactive", etc.
	StartType   string `json:"start_type"`   // "auto", "manual", "disabled", "enabled", etc.
	Path        string `json:"path"`         // Executable / ExecStart binary path
	User        string `json:"user"`         // Service account
	Description string `json:"description"`
	Source      string `json:"source"`       // "windows_service", "systemd", "init.d"
}

// ServiceCollector enumerates installed and running system services in a strictly read-only manner.
type ServiceCollector struct{}

// NewServiceCollector creates an initialized ServiceCollector.
func NewServiceCollector() *ServiceCollector {
	return &ServiceCollector{}
}

func (c *ServiceCollector) Name() string {
	return "services"
}

func (c *ServiceCollector) Supports(target string) bool {
	t := strings.ToLower(strings.TrimSpace(target))
	return t == "services" || t == "service"
}

// Collect enumerates services without modifying, starting, or stopping any service.
func (c *ServiceCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	entries, err := collectServices(ctx, request.Parameters)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, s := range entries {
		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        "service",
			CollectedAt: now,
			Data: map[string]interface{}{
				"name":         s.Name,
				"display_name": s.DisplayName,
				"status":       s.Status,
				"start_type":   s.StartType,
				"path":         s.Path,
				"user":         s.User,
				"description":  s.Description,
				"source":       s.Source,
			},
		})
	}

	return artifacts, nil
}

// ParseScQueryOutput parses Windows `sc query state= all` or `sc queryex type= service state= all` output.
func ParseScQueryOutput(output string) []ServiceEntry {
	var entries []ServiceEntry
	lines := strings.Split(output, "\n")

	var current *ServiceEntry

	for _, rawLine := range lines {
		line := strings.TrimSpace(rawLine)
		if line == "" {
			continue
		}

		if strings.HasPrefix(line, "SERVICE_NAME:") {
			if current != nil && current.Name != "" {
				entries = append(entries, *current)
			}
			name := strings.TrimSpace(strings.TrimPrefix(line, "SERVICE_NAME:"))
			current = &ServiceEntry{
				Name:        name,
				DisplayName: name,
				Status:      "unknown",
				StartType:   "unknown",
				Source:      "windows_service",
			}
			continue
		}

		if current == nil {
			continue
		}

		if strings.HasPrefix(line, "DISPLAY_NAME:") {
			current.DisplayName = strings.TrimSpace(strings.TrimPrefix(line, "DISPLAY_NAME:"))
		} else if strings.HasPrefix(line, "STATE") {
			parts := strings.SplitN(line, ":", 2)
			if len(parts) == 2 {
				val := strings.TrimSpace(parts[1])
				// e.g., "4  RUNNING", "1  STOPPED"
				fields := strings.Fields(val)
				if len(fields) >= 2 {
					current.Status = strings.ToLower(fields[1])
				} else if len(fields) == 1 {
					current.Status = strings.ToLower(fields[0])
				}
			}
		}
	}

	if current != nil && current.Name != "" {
		entries = append(entries, *current)
	}

	return entries
}

// ParseSystemctlListUnits parses Linux `systemctl list-units --type=service --all --no-pager --no-legend` output.
func ParseSystemctlListUnits(output string) []ServiceEntry {
	var entries []ServiceEntry
	lines := strings.Split(output, "\n")

	for _, rawLine := range lines {
		line := strings.TrimSpace(rawLine)
		if line == "" || strings.HasPrefix(line, "●") {
			// Some systemctl output prepends bullet dot for failed units
			line = strings.TrimSpace(strings.TrimPrefix(line, "●"))
		}
		if line == "" || strings.HasPrefix(line, "UNIT") || strings.HasPrefix(line, "LOAD") {
			continue
		}

		fields := strings.Fields(line)
		if len(fields) < 4 {
			continue
		}

		unit := fields[0]
		if !strings.HasSuffix(unit, ".service") {
			continue
		}

		name := strings.TrimSuffix(unit, ".service")
		activeState := fields[2]
		subState := fields[3]
		desc := ""
		if len(fields) > 4 {
			desc = strings.Join(fields[4:], " ")
		}

		status := activeState
		if subState != "" && subState != activeState {
			status = activeState + "/" + subState
		}

		entries = append(entries, ServiceEntry{
			Name:        name,
			DisplayName: unit,
			Status:      strings.ToLower(status),
			StartType:   "systemd",
			Description: desc,
			Source:      "systemd",
		})
	}

	return entries
}

// ParseSystemdUnitFile parses an individual systemd service unit file content.
func ParseSystemdUnitFile(content string, unitName string) *ServiceEntry {
	lines := strings.Split(content, "\n")
	var desc, execStart, user string
	name := strings.TrimSuffix(unitName, ".service")

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, ";") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		k := strings.TrimSpace(parts[0])
		v := strings.TrimSpace(parts[1])

		switch strings.ToLower(k) {
		case "description":
			desc = v
		case "execstart":
			execStart = v
		case "user":
			user = v
		}
	}

	if desc == "" && execStart == "" && user == "" {
		return nil
	}

	return &ServiceEntry{
		Name:        name,
		DisplayName: unitName,
		Status:      "installed",
		StartType:   "systemd",
		Path:        execStart,
		User:        user,
		Description: desc,
		Source:      "systemd",
	}
}
