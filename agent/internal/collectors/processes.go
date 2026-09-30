package collectors

import (
	"context"
	"strconv"
	"strings"
	"time"
)

// ProcessInfo represents normalized metadata for a running process.
type ProcessInfo struct {
	PID             int    `json:"pid"`
	Name            string `json:"name"`
	Path            string `json:"path"`
	ParentPID       int    `json:"parent_pid"`
	PPID            int    `json:"ppid,omitempty"`
	User            string `json:"user"`
	CommandLine     string `json:"command_line"`
	SignatureStatus string `json:"signature_status"` // "signed", "unsigned", "unsupported", "unknown"
}

// ProcessEntry is an alias for ProcessInfo to maintain compatibility with legacy tests.
type ProcessEntry = ProcessInfo

// ProcessCollector is a read-only forensic collector for host processes.
type ProcessCollector struct{}

// NewProcessCollector creates a new ProcessCollector instance.
func NewProcessCollector() *ProcessCollector {
	return &ProcessCollector{}
}

func (c *ProcessCollector) Name() string {
	return "processes"
}

func (c *ProcessCollector) Supports(target string) bool {
	return target == "processes"
}

func (c *ProcessCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}

	procs, err := collectPlatformProcesses(ctx)
	if err != nil {
		return nil, err
	}

	artifacts := make([]Artifact, 0, len(procs))
	now := time.Now().UTC()

	for _, p := range procs {
		// Check for context cancellation during processing
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}

		ppid := p.ParentPID
		if ppid == 0 && p.PPID != 0 {
			ppid = p.PPID
		}

		data := map[string]any{
			"pid":              p.PID,
			"name":             p.Name,
			"path":             p.Path,
			"parent_pid":       ppid,
			"ppid":             ppid,
			"user":             p.User,
			"command_line":     p.CommandLine,
			"signature_status": p.SignatureStatus,
		}

		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        "process",
			CollectedAt: now,
			Data:        data,
		})
	}

	return artifacts, nil
}

// ParseLinuxPsOutput parses standard Linux `ps -eo pid,ppid,user,args` output into ProcessInfo records.
func ParseLinuxPsOutput(output string) []ProcessInfo {
	lines := strings.Split(output, "\n")
	var entries []ProcessInfo

	for i, line := range lines {
		line = strings.TrimSpace(line)
		if i == 0 || line == "" {
			continue // skip header or blank
		}

		fields := strings.Fields(line)
		if len(fields) < 4 {
			continue
		}

		pid, _ := strconv.Atoi(fields[0])
		ppid, _ := strconv.Atoi(fields[1])
		user := fields[2]
		cmdline := strings.Join(fields[3:], " ")
		name := fields[3]
		// extract basename
		if slashIdx := strings.LastIndex(name, "/"); slashIdx != -1 {
			name = name[slashIdx+1:]
		}

		entries = append(entries, ProcessInfo{
			PID:             pid,
			ParentPID:       ppid,
			PPID:            ppid,
			Name:            name,
			Path:            fields[3],
			CommandLine:     cmdline,
			User:            user,
			SignatureStatus: "unsupported",
		})
	}

	return entries
}
