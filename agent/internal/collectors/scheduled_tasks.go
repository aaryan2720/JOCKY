package collectors

import (
	"context"
	"encoding/csv"
	"fmt"
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
	User      string `json:"user"`
	Enabled   bool   `json:"enabled"`
	Source    string `json:"source"` // "schtasks", "cron", "systemd_timer"
}

// ScheduledTaskCollector collects scheduled tasks and cron jobs.
type ScheduledTaskCollector struct{}

// NewScheduledTaskCollector creates a new ScheduledTaskCollector.
func NewScheduledTaskCollector() *ScheduledTaskCollector {
	return &ScheduledTaskCollector{}
}

func (c *ScheduledTaskCollector) Name() string {
	return "scheduled_tasks"
}

func (c *ScheduledTaskCollector) Supports(target string) bool {
	return target == "scheduled_tasks" || target == "cron" || target == "tasks"
}

func (c *ScheduledTaskCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	entries, err := collectScheduledTasks(ctx, request.Parameters)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, task := range entries {
		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        "scheduled_task",
			CollectedAt: now,
			Data: map[string]interface{}{
				"name":      task.Name,
				"path":      task.Path,
				"author":    task.Author,
				"action":    task.Action,
				"arguments": task.Arguments,
				"trigger":   task.Trigger,
				"user":      task.User,
				"enabled":   task.Enabled,
				"source":    task.Source,
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
	var colMap map[string]int

	for {
		record, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		if colMap == nil {
			colMap = make(map[string]int)
			for i, col := range record {
				colMap[strings.ToLower(strings.TrimSpace(col))] = i
			}
			continue
		}

		getVal := func(keys ...string) string {
			for _, k := range keys {
				if idx, ok := colMap[strings.ToLower(k)]; ok && idx < len(record) {
					v := strings.TrimSpace(record[idx])
					if v != "" && v != "N/A" {
						return v
					}
				}
			}
			return ""
		}

		taskName := getVal("taskname", "task name")
		if taskName == "" && len(record) > 1 {
			taskName = strings.TrimSpace(record[1])
		}
		if taskName == "" {
			continue
		}

		status := getVal("status", "scheduled task state")
		author := getVal("author")
		action := getVal("task to run", "action")
		user := getVal("run as user", "user")

		enabled := !strings.EqualFold(status, "Disabled")

		entries = append(entries, ScheduledTaskEntry{
			Name:    taskName,
			Author:  author,
			Action:  action,
			User:    user,
			Enabled: enabled,
			Source:  "schtasks",
		})
	}

	return entries
}

// ParseCrontab parses /etc/crontab or crontab file content into ScheduledTaskEntry.
func ParseCrontab(content string, sourcePath string) []ScheduledTaskEntry {
	lines := strings.Split(content, "\n")
	var entries []ScheduledTaskEntry

	for _, line := range lines {
		entry, err := ParseCronLine(line, sourcePath)
		if err != nil || entry == nil {
			continue
		}
		entries = append(entries, *entry)
	}

	return entries
}

// ParseCronLine parses a single line of crontab.
func ParseCronLine(line string, sourcePath string) (*ScheduledTaskEntry, error) {
	line = strings.TrimSpace(line)
	if line == "" || strings.HasPrefix(line, "#") {
		return nil, nil
	}

	// Format: minute hour dom month dow [user] command
	fields := strings.Fields(line)
	if len(fields) < 6 {
		return nil, fmt.Errorf("insufficient fields in cron line")
	}

	// Detect if system crontab (has username field) or user crontab
	trigger := strings.Join(fields[:5], " ")
	var user, action, args string

	if len(fields) >= 7 && !strings.HasPrefix(fields[5], "/") {
		user = fields[5]
		action = fields[6]
		if len(fields) > 7 {
			args = strings.Join(fields[7:], " ")
		}
	} else {
		user = "root"
		action = fields[5]
		if len(fields) > 6 {
			args = strings.Join(fields[6:], " ")
		}
	}

	name := fmt.Sprintf("%s:%s", sourcePath, action)
	if len(args) > 0 {
		action = action + " " + args
	}

	return &ScheduledTaskEntry{
		Name:      name,
		Path:      sourcePath,
		Trigger:   trigger,
		User:      user,
		Action:    action,
		Arguments: args,
		Enabled:   true,
		Source:    "cron",
	}, nil
}
