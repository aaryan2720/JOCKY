package collectors

import (
	"context"
	"fmt"
	"time"
)

// PlaceholderCollector provides a safe implementation for unimplemented collector targets.
type PlaceholderCollector struct {
	targetName string
}

// NewPlaceholderCollector creates a placeholder collector for the given target.
func NewPlaceholderCollector(targetName string) *PlaceholderCollector {
	return &PlaceholderCollector{targetName: targetName}
}

func (p *PlaceholderCollector) Name() string {
	return p.targetName
}

func (p *PlaceholderCollector) Supports(target string) bool {
	return target == p.targetName
}

// Collect returns placeholder metadata without crashing or failing.
func (p *PlaceholderCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}

	return []Artifact{
		{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        p.targetName,
			CollectedAt: time.Now().UTC(),
			Data: map[string]interface{}{
				"status":  "placeholder",
				"message": fmt.Sprintf("Collector %s is a placeholder in this phase", p.targetName),
			},
		},
	}, nil
}
