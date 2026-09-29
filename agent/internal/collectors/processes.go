package collectors

import (
	"context"
	"time"
)

// ProcessInfo represents normalized metadata for a running process.
type ProcessInfo struct {
	PID             int    `json:"pid"`
	Name            string `json:"name"`
	Path            string `json:"path"`
	ParentPID       int    `json:"parent_pid"`
	User            string `json:"user"`
	CommandLine     string `json:"command_line"`
	SignatureStatus string `json:"signature_status"` // "signed", "unsigned", "unsupported", "unknown"
}

// ProcessCollector is a read-only forensic collector for host processes.
type ProcessCollector struct{}

// NewProcessCollector creates a new ProcessCollector instance.
func NewProcessCollector() *ProcessCollector {
	return &ProcessCollector{}
}

func (c *ProcessCollector) Name() string {
	return "process-collector"
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

		data := map[string]any{
			"pid":              p.PID,
			"name":             p.Name,
			"path":             p.Path,
			"parent_pid":       p.ParentPID,
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
