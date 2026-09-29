package runtime

import (
	"context"
	"log"

	"github.com/jocky-dfir/jocky/agent/internal/collectors"
	"github.com/jocky-dfir/jocky/agent/internal/detection"
	"github.com/jocky-dfir/jocky/agent/internal/registration"
	"github.com/jocky-dfir/jocky/agent/internal/transport"
)

// AgentRuntime coordinates collectors, transport, and execution cycles.
type AgentRuntime struct {
	Identity   *registration.Identity
	Transport  transport.Transport
	Collectors map[string]collectors.Collector
	Detection  detection.LocalEngine
}

// NewRuntime initializes a new forensic agent runtime.
func NewRuntime(identity *registration.Identity) *AgentRuntime {
	return &AgentRuntime{
		Identity:   identity,
		Collectors: make(map[string]collectors.Collector),
	}
}

// ExecutePlan executes a compiled JOCKY plan on the local host.
func (r *AgentRuntime) ExecutePlan(ctx context.Context, plan map[string]interface{}) error {
	log.Printf("[Agent Runtime] Executing JOCKY plan...")
	// Forensic collection execution will be implemented in subsequent phase
	return nil
}

// Start begins the agent heartbeat and listening loop.
func (r *AgentRuntime) Start(ctx context.Context) error {
	log.Printf("[Agent Runtime] Initialized for %s (%s/%s)", r.Identity.Hostname, r.Identity.OS, r.Identity.Arch)
	return nil
}
