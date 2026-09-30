package runtime

import (
	"context"
	"fmt"
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
	Registry   *collectors.Registry
	Collectors map[string]collectors.Collector
	Detection  detection.LocalEngine
}

// NewRuntime initializes a new forensic agent runtime with registered collectors.
func NewRuntime(identity *registration.Identity) *AgentRuntime {
	reg := collectors.NewDefaultRegistry()
	return &AgentRuntime{
		Identity:   identity,
		Registry:   reg,
		Collectors: reg.All(),
	}
}

// ExecutePlanArtifacts runs the collectors specified in a compiled JOCKY plan and returns the collected artifacts.
func (r *AgentRuntime) ExecutePlanArtifacts(ctx context.Context, plan map[string]interface{}) ([]collectors.Artifact, error) {
	log.Printf("[Agent Runtime] Executing JOCKY plan...")
	var allArtifacts []collectors.Artifact

	var requested []string
	if rawCollectors, ok := plan["collectors"].([]interface{}); ok {
		for _, item := range rawCollectors {
			if s, ok := item.(string); ok {
				requested = append(requested, s)
			} else if m, ok := item.(map[string]interface{}); ok {
				if n, ok := m["name"].(string); ok {
					requested = append(requested, n)
				}
			}
		}
	} else if strList, ok := plan["collectors"].([]string); ok {
		requested = strList
	}

	if len(requested) == 0 {
		return allArtifacts, nil
	}

	for _, name := range requested {
		if err := ctx.Err(); err != nil {
			return allArtifacts, fmt.Errorf("execution plan cancelled: %w", err)
		}

		collector, exists := r.Collectors[name]
		if !exists {
			if r.Registry != nil {
				collector, exists = r.Registry.Get(name)
			}
		}

		if !exists {
			log.Printf("[Agent Runtime] Collector '%s' not registered, skipping", name)
			continue
		}

		log.Printf("[Agent Runtime] Running collector '%s'...", name)
		artifacts, err := collector.Collect(ctx, nil)
		if err != nil {
			log.Printf("[Agent Runtime] Collector '%s' error: %v (continuing)", name, err)
			continue
		}

		allArtifacts = append(allArtifacts, artifacts...)
	}

	// Submit via transport if configured
	if r.Transport != nil && len(allArtifacts) > 0 {
		jobID, _ := plan["job_id"].(string)
		if jobID == "" {
			jobID = "plan-job"
		}
		agentID := ""
		if r.Identity != nil {
			agentID = r.Identity.AgentID
		}
		if err := r.Transport.SubmitArtifacts(ctx, jobID, agentID, allArtifacts); err != nil {
			log.Printf("[Agent Runtime] Failed to submit artifacts: %v", err)
		}
	}

	return allArtifacts, nil
}

// ExecutePlan executes a compiled JOCKY plan on the local host.
func (r *AgentRuntime) ExecutePlan(ctx context.Context, plan map[string]interface{}) error {
	_, err := r.ExecutePlanArtifacts(ctx, plan)
	return err
}

// Start begins the agent heartbeat and listening loop.
func (r *AgentRuntime) Start(ctx context.Context) error {
	log.Printf("[Agent Runtime] Initialized for %s (%s/%s)", r.Identity.Hostname, r.Identity.OS, r.Identity.Arch)
	return nil
}
