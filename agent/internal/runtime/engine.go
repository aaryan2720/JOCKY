package runtime

import (
	"context"
	"fmt"
	"log"
	"sync"

	"github.com/jocky-dfir/jocky/agent/internal/collectors"
	"github.com/jocky-dfir/jocky/agent/internal/detection"
	"github.com/jocky-dfir/jocky/agent/internal/registration"
	"github.com/jocky-dfir/jocky/agent/internal/transport"
)

// CollectionResult encapsulates the forensic output or error from an individual collector run.
type CollectionResult struct {
	Target    string                `json:"target"`
	Artifacts []collectors.Artifact `json:"artifacts"`
	Error     error                 `json:"error,omitempty"`
}

// ExecutionResult encapsulates the consolidated results and instructions of a plan execution cycle.
type ExecutionResult struct {
	JobID             string             `json:"job_id"`
	AgentID           string             `json:"agent_id"`
	PlanVersion       string             `json:"plan_version"`
	CollectionResults []CollectionResult `json:"collection_results"`
	ParsedPlan        *ParsedPlan        `json:"parsed_plan"`
}

// AgentRuntime coordinates collector registries, execution plans, and local execution cycles.
type AgentRuntime struct {
	Identity  *registration.Identity
	Transport transport.Transport
	Registry  *collectors.Registry
	Detection detection.LocalEngine
}

// NewRuntime initializes a new forensic agent runtime with the default collector registry.
func NewRuntime(identity *registration.Identity) *AgentRuntime {
	return &AgentRuntime{
		Identity: identity,
		Registry: collectors.NewDefaultRegistry(),
	}
}

// ExecutePlan validates, translates, and concurrently executes forensic collection requests.
func (r *AgentRuntime) ExecutePlan(ctx context.Context, plan *ExecutionPlan) (*ExecutionResult, error) {
	if err := ValidatePlan(plan); err != nil {
		return nil, fmt.Errorf("plan validation failed: %w", err)
	}

	agentID := ""
	if r.Identity != nil {
		agentID = r.Identity.AgentID
	}

	parsed, err := TranslatePlan(plan, "job-local", agentID)
	if err != nil {
		return nil, fmt.Errorf("failed to translate plan: %w", err)
	}

	execResult := &ExecutionResult{
		JobID:             "job-local",
		AgentID:           agentID,
		PlanVersion:       plan.Version,
		CollectionResults: make([]CollectionResult, 0, len(parsed.CollectionRequests)),
		ParsedPlan:        parsed,
	}

	if len(parsed.CollectionRequests) == 0 {
		return execResult, nil
	}

	// Concurrency orchestration for collection requests
	var wg sync.WaitGroup
	resultChan := make(chan CollectionResult, len(parsed.CollectionRequests))

	for _, req := range parsed.CollectionRequests {
		wg.Add(1)
		go func(rReq collectors.CollectionRequest) {
			defer wg.Done()

			// Check context cancellation before starting
			if ctx.Err() != nil {
				resultChan <- CollectionResult{
					Target: rReq.Target,
					Error:  ctx.Err(),
				}
				return
			}

			col, found := r.Registry.Resolve(rReq.Target)
			if !found {
				resultChan <- CollectionResult{
					Target: rReq.Target,
					Error:  fmt.Errorf("no registered collector supports target %q", rReq.Target),
				}
				return
			}

			artifacts, colErr := col.Collect(ctx, rReq)
			resultChan <- CollectionResult{
				Target:    rReq.Target,
				Artifacts: artifacts,
				Error:     colErr,
			}
		}(req)
	}

	wg.Wait()
	close(resultChan)

	for res := range resultChan {
		execResult.CollectionResults = append(execResult.CollectionResults, res)
	}

	return execResult, nil
}

// Start begins the agent lifecycle and heartbeat monitor.
func (r *AgentRuntime) Start(ctx context.Context) error {
	hostname := "unknown"
	osType := "unknown"
	arch := "unknown"
	if r.Identity != nil {
		hostname = r.Identity.Hostname
		osType = r.Identity.OS
		arch = r.Identity.Arch
	}
	log.Printf("[Agent Runtime] Initialized for %s (%s/%s)", hostname, osType, arch)
	return nil
}
