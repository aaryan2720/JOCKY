package collectors

import (
	"context"
	"encoding/csv"
	"io"
	"strings"
	"time"
)

// ScheduledTaskEntry represents a normalized scheduled task or cron job.
type ScheduledTaskEntry struct {
	Name      string `json:"name"`
	Path      string `json:"path"`
	Author    string `json:"author"`
	Action    string `json:"action"`
	Arguments string `json:"arguments"`
	Trigger   string `json:"trigger"`
	Enabled   bool   `json:"enabled"`
	User      string `json:"user"`
}

// ScheduledTaskCollector collects scheduled tasks (Windows) and cron entries (Linux).
type ScheduledTaskCollector struct{}

// NewScheduledTaskCollector creates a new ScheduledTaskCollector instance.
func NewScheduledTaskCollector() *ScheduledTaskCollector {
	return &ScheduledTaskCollector{}
}

func (c *ScheduledTaskCollector) Name() string {
	return "scheduled_tasks"
}

// Collect enumerates scheduled tasks and crontabs in read-only mode.
func (c *ScheduledTaskCollector) Collect(ctx context.Context, options map[string]interface{}) ([]Artifact, error) {
	entries, err := collectScheduledTasks(ctx, options)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, t := range entries {
		artifacts = append(artifacts, Artifact{
			Type:        "scheduled_task",
			CollectedAt: now,
			Data: map[string]interface{}{
				"name":      t.Name,
				"path":      t.Path,
				"author":    t.Author,
				"action":    t.Action,
				"arguments": t.Arguments,
				"trigger":   t.Trigger,
				"enabled":   t.Enabled,
				"user":      t.User,
			},
		})
	}

	return artifacts, nil
}

// ParseSchtasksCSV parses standard Windows `schtasks /query /fo CSV /v` output.
func ParseSchtasksCSV(csvData string) []ScheduledTaskEntry {
	r := csv.NewReader(strings.NewReader(csvData))
	r.FieldsPerRecord = -1
	r.LazyQuotes = true

	var entries []ScheduledTaskEntry
	var headers []string

	for {
		record, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}

		if headers == nil {
			headers = make([]string, len(record))
			for i, h := range record {
				headers[i] = strings.ToLower(strings.TrimSpace(h))
			}
			continue
		}

		// Map fields by header names
		var name, path, author, action, trigger, user, status string

		for i, val := range record {
			if i >= len(headers) {
				break
			}
			val = strings.TrimSpace(val)
			switch headers[i] {
			case "taskname":
				name = val
				path = val
			case "author":
				author = val
			case "task to run", "action":
				action = val
			case "schedule type", "trigger":
				trigger = val
			case "run as user", "user":
				user = val
			case "status":
				status = val
			}
		}

		if name == "" && action == "" {
			continue
		}

		enabled := true
		if strings.EqualFold(status, "Disabled") {
			enabled = false
		}

		// Split command action into binary and arguments if applicable
		args := ""
		if spaceIdx := strings.Index(action, " "); spaceIdx != -1 {
			args = action[spaceIdx+1:]
		}

		entries = append(entries, ScheduledTaskEntry{
			Name:      name,
			Path:      path,
			Author:    author,
			Action:    action,
			Arguments: args,
			Trigger:   trigger,
			Enabled:   enabled,
			User:      user,
		})
	}

	return entries
}

// ParseCrontab parses a crontab file content into ScheduledTaskEntry records.
func ParseCrontab(content string, sourcePath string) []ScheduledTaskEntry {
	lines := strings.Split(content, "\n")
	var entries []ScheduledTaskEntry

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") || strings.Contains(line, "=") {
			continue
		}

		entry, err := ParseCronLine(line, sourcePath)
		if err == nil && entry != nil {
			entries = append(entries, *entry)
		}
	}

	return entries
}

// ParseCronLine parses a single cron line (e.g. `0 * * * * root /bin/backup.sh`).
func ParseCronLine(line string, sourcePath string) (*ScheduledTaskEntry, error) {
	fields := strings.Fields(line)
	// System crontab format: m h dom mon dow user command... (min 7 fields)
	// User crontab format: m h dom mon dow command... (min 6 fields)
	if len(fields) < 6 {
		return nil, nil
	}

	trigger := strings.Join(fields[0:5], " ")
	var user string
	var commandParts []string

	if len(fields) >= 7 {
		user = fields[5]
		commandParts = fields[6:]
	} else {
		user = "current_user"
		commandParts = fields[5:]
	}

	action := strings.Join(commandParts, " ")
	args := ""
	if len(commandParts) > 1 {
		args = strings.Join(commandParts[1:], " ")
	}

	return &ScheduledTaskEntry{
		Name:      sourcePath + ":" + commandParts[0],
		Path:      sourcePath,
		Author:    user,
		Action:    action,
		Arguments: args,
		Trigger:   trigger,
		Enabled:   true,
		User:      user,
	}, nil
}
