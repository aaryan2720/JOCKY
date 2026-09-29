package collectors

import (
	"context"
	"time"
)

// Artifact represents structured forensic telemetry collected from the host.
type Artifact struct {
	Type        string                 `json:"type"`
	CollectedAt time.Time              `json:"collected_at"`
	Data        map[string]interface{} `json:"data"`
}

// Collector is the unified interface implemented by all forensic telemetry collectors.
// Strictly read-only operations.
type Collector interface {
	Name() string
	Collect(ctx context.Context, options map[string]interface{}) ([]Artifact, error)
}
