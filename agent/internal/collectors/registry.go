package collectors

import (
	"sort"
	"sync"
)

// Registry manages the set of available forensic telemetry collectors.
type Registry struct {
	mu         sync.RWMutex
	collectors map[string]Collector
	list       []Collector
}

// NewRegistry initializes an empty collector registry.
func NewRegistry() *Registry {
	return &Registry{
		collectors: make(map[string]Collector),
		list:       make([]Collector, 0),
	}
}

// Register adds or replaces a collector in the registry.
func (r *Registry) Register(c Collector) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.collectors[c.Name()] = c
	r.list = append(r.list, c)
}

// Resolve returns the first registered collector that supports the given target.
func (r *Registry) Resolve(target string) (Collector, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	if c, ok := r.collectors[target]; ok {
		return c, true
	}
	for _, c := range r.list {
		if c.Supports(target) {
			return c, true
		}
	}
	return nil, false
}

// Get retrieves a collector by name.
func (r *Registry) Get(name string) (Collector, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	c, ok := r.collectors[name]
	if !ok {
		return r.Resolve(name)
	}
	return c, ok
}

// List returns a sorted list of registered collector names.
func (r *Registry) List() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	names := make([]string, 0, len(r.collectors))
	for name := range r.collectors {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

// All returns a shallow copy of all registered collectors.
func (r *Registry) All() map[string]Collector {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make(map[string]Collector, len(r.collectors))
	for k, v := range r.collectors {
		out[k] = v
	}
	return out
}

// IsPlaceholder returns true if the named collector is a placeholder.
func (r *Registry) IsPlaceholder(name string) bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	c, ok := r.collectors[name]
	if !ok {
		return false
	}
	_, isPlaceholder := c.(*PlaceholderCollector)
	return isPlaceholder
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

// PlaceholderTargets lists targets that remain scaffolded as placeholders.
var PlaceholderTargets = []string{
	"files",
	"drivers",
	"services",
	"event_logs",
}

// NewDefaultRegistry instantiates the default registry with all collectors.
func NewDefaultRegistry() *Registry {
	r := NewRegistry()

	// 1. Real collectors
	r.Register(NewProcessCollector())
	r.Register(NewConnectionCollector())
	r.Register(NewAutorunCollector())
	r.Register(NewScheduledTaskCollector())
	r.Register(NewUserCollector())
	r.Register(NewSessionCollector())

	// 2. Placeholder collectors
	r.Register(NewPlaceholderCollector("files"))
	r.Register(NewPlaceholderCollector("drivers"))
	r.Register(NewPlaceholderCollector("services"))
	r.Register(NewPlaceholderCollector("event_logs"))

	return r
}
