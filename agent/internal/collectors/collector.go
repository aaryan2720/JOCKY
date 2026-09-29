package collectors

import (
	"context"
	"errors"
	"time"
)

// ErrNotImplemented is returned by placeholder collectors to ensure no fake forensic data is generated.
var ErrNotImplemented = errors.New("forensic collector is not implemented yet")

// Artifact represents a structured piece of forensic evidence collected from an endpoint.
type Artifact struct {
	ID          string         `json:"id,omitempty"`
	JobID       string         `json:"job_id,omitempty"`
	AgentID     string         `json:"agent_id,omitempty"`
	Type        string         `json:"type"`
	CollectedAt time.Time      `json:"collected_at"`
	Data        map[string]any `json:"data"`
}

// Condition represents a filter or predicate passed to a collector.
type Condition struct {
	Field      string      `json:"field,omitempty"`
	Operator   string      `json:"operator"` // eq, neq, gt, lt, gte, lte, contains, in, and, or
	Value      any         `json:"value,omitempty"`
	Conditions []Condition `json:"conditions,omitempty"`
}

// CollectionRequest carries the target, filters, and read-only parameters for a collector.
type CollectionRequest struct {
	JobID      string         `json:"job_id,omitempty"`
	AgentID    string         `json:"agent_id,omitempty"`
	Target     string         `json:"target"`
	Conditions []Condition    `json:"conditions,omitempty"`
	Parameters map[string]any `json:"parameters,omitempty"`
}

// Collector is the unified abstraction implemented by all forensic telemetry collectors.
// Strictly read-only operations. OS-specific implementations remain isolated behind this interface.
type Collector interface {
	Name() string
	Supports(target string) bool
	Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error)
}
