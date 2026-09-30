package collectors

import (
	"context"
	"time"
)

// PlaceholderCollector provides a safe no-op implementation for unimplemented collector targets.
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

// Collect returns an empty artifact slice or placeholder metadata without failure.
func (p *PlaceholderCollector) Collect(ctx context.Context, options map[string]interface{}) ([]Artifact, error) {
	// Strictly non-blocking and read-only. Returns empty artifacts for placeholders.
	_ = ctx
	_ = options
	return []Artifact{
		{
			Type:        p.targetName,
			CollectedAt: time.Now().UTC(),
			Data: map[string]interface{}{
				"status":  "placeholder",
				"message": "Collector " + p.targetName + " is a placeholder in this phase",
			},
		},
	}, nil
}
