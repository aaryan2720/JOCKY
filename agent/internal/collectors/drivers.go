package collectors

import (
	"context"
	"encoding/csv"
	"io"
	"strconv"
	"strings"
	"time"
)

// DriverEntry represents a normalized kernel driver or module artifact.
type DriverEntry struct {
	Name        string   `json:"name"`
	DisplayName string   `json:"display_name"`
	State       string   `json:"state"`       // "running", "stopped", "Live", "loaded", etc.
	Path        string   `json:"path"`        // Driver image path (.sys on Windows, .ko on Linux)
	Type        string   `json:"type"`        // "Kernel", "File System", "kernel_module"
	Size        int64    `json:"size"`        // Size in bytes
	UsageCount  int      `json:"usage_count"` // Usage reference count
	DependsOn   []string `json:"depends_on"`  // Dependent modules / drivers
	Source      string   `json:"source"`      // "driverquery", "proc_modules", "lsmod"
}

// DriverCollector enumerates installed and loaded kernel drivers and modules in a strictly read-only manner.
type DriverCollector struct{}

// NewDriverCollector creates an initialized DriverCollector.
func NewDriverCollector() *DriverCollector {
	return &DriverCollector{}
}

func (c *DriverCollector) Name() string {
	return "drivers"
}

func (c *DriverCollector) Supports(target string) bool {
	t := strings.ToLower(strings.TrimSpace(target))
	return t == "drivers" || t == "driver" || t == "kernel_modules" || t == "modules"
}

// Collect enumerates drivers/modules without loading, unloading, or modifying any kernel state.
func (c *DriverCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	entries, err := collectDrivers(ctx, request.Parameters)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, d := range entries {
		depends := d.DependsOn
		if depends == nil {
			depends = []string{}
		}

		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        "driver",
			CollectedAt: now,
			Data: map[string]interface{}{
				"name":         d.Name,
				"display_name": d.DisplayName,
				"state":        d.State,
				"path":         d.Path,
				"type":         d.Type,
				"size":         d.Size,
				"usage_count":  d.UsageCount,
				"depends_on":   depends,
				"source":       d.Source,
			},
		})
	}

	return artifacts, nil
}

// ParseDriverQueryCSV parses Windows `driverquery /fo CSV` or `driverquery /fo CSV /v` output.
func ParseDriverQueryCSV(csvData string) []DriverEntry {
	r := csv.NewReader(strings.NewReader(csvData))
	r.FieldsPerRecord = -1
	r.LazyQuotes = true

	var entries []DriverEntry
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

		name := getVal("module name", "driver name", "name")
		if name == "" && len(record) > 0 {
			name = strings.TrimSpace(record[0])
		}
		if name == "" {
			continue
		}

		dispName := getVal("display name")
		if dispName == "" {
			dispName = name
		}

		driverType := getVal("driver type", "type")
		if driverType == "" {
			driverType = "Kernel"
		}

		state := getVal("state", "status")
		if state == "" {
			state = "Running"
		}

		path := getVal("path", "image path")

		entries = append(entries, DriverEntry{
			Name:        name,
			DisplayName: dispName,
			State:       state,
			Path:        path,
			Type:        driverType,
			DependsOn:   []string{},
			Source:      "driverquery",
		})
	}

	return entries
}

// ParseProcModules parses Linux `/proc/modules` content into DriverEntry structures.
func ParseProcModules(content string) []DriverEntry {
	lines := strings.Split(content, "\n")
	var entries []DriverEntry

	for _, rawLine := range lines {
		line := strings.TrimSpace(rawLine)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		fields := strings.Fields(line)
		if len(fields) < 3 {
			continue
		}

		name := fields[0]
		size, _ := strconv.ParseInt(fields[1], 10, 64)
		usageCount, _ := strconv.Atoi(fields[2])

		var depends []string
		if len(fields) >= 4 && fields[3] != "-" && fields[3] != "" {
			rawDeps := strings.Split(fields[3], ",")
			for _, d := range rawDeps {
				dClean := strings.TrimSpace(d)
				if dClean != "" {
					depends = append(depends, dClean)
				}
			}
		}
		if depends == nil {
			depends = []string{}
		}

		state := "Live"
		if len(fields) >= 5 {
			state = fields[4]
		}

		entries = append(entries, DriverEntry{
			Name:        name,
			DisplayName: name,
			State:       state,
			Path:        "",
			Type:        "kernel_module",
			Size:        size,
			UsageCount:  usageCount,
			DependsOn:   depends,
			Source:      "proc_modules",
		})
	}

	return entries
}
