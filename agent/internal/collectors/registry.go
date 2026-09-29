package collectors

import (
	"context"
	"fmt"
	"sync"
)

// PlaceholderCollector is a placeholder implementation that explicitly returns ErrNotImplemented.
// Stubs must never return fabricated or fake forensic telemetry.
type PlaceholderCollector struct {
	targetName string
}

// NewPlaceholderCollector creates a placeholder collector for a specific target.
func NewPlaceholderCollector(targetName string) *PlaceholderCollector {
	return &PlaceholderCollector{targetName: targetName}
}

func (p *PlaceholderCollector) Name() string {
	return fmt.Sprintf("placeholder-%s", p.targetName)
}

func (p *PlaceholderCollector) Supports(target string) bool {
	return target == p.targetName
}

func (p *PlaceholderCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
		return nil, fmt.Errorf("%w: collector for target %q is not implemented in this phase", ErrNotImplemented, p.targetName)
	}
}

// Registry maintains the collection of active forensic collectors.
type Registry struct {
	mu         sync.RWMutex
	collectors []Collector
}

// NewRegistry initializes an empty collector registry.
func NewRegistry() *Registry {
	return &Registry{
		collectors: make([]Collector, 0),
	}
}

// Register adds a collector to the registry.
func (r *Registry) Register(c Collector) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.collectors = append(r.collectors, c)
}

// Resolve returns the first registered collector that supports the given target.
func (r *Registry) Resolve(target string) (Collector, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	for _, c := range r.collectors {
		if c.Supports(target) {
			return c, true
		}
	}
	return nil, false
}

// List returns the names of all registered collectors.
func (r *Registry) List() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	names := make([]string, 0, len(r.collectors))
	for _, c := range r.collectors {
		names = append(names, c.Name())
	}
	return names
}

// DefaultTargets lists the 10 core forensic targets supported by JOCKY.
var DefaultTargets = []string{
	"processes",
	"connections",
	"files",
	"drivers",
	"services",
	"autoruns",
	"scheduled_tasks",
	"users",
	"sessions",
	"event_logs",
}

// NewDefaultRegistry initializes a registry populated with the 10 placeholder collectors.
func NewDefaultRegistry() *Registry {
	reg := NewRegistry()
	for _, target := range DefaultTargets {
		reg.Register(NewPlaceholderCollector(target))
	}
	return reg
}
