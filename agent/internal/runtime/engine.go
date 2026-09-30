package runtime

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

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

// ExecuteJob validates, translates, and concurrently executes forensic collection requests for a specific job ID.
func (r *AgentRuntime) ExecuteJob(ctx context.Context, jobID string, plan *ExecutionPlan) (*ExecutionResult, error) {
	if err := ValidatePlan(plan); err != nil {
		return nil, fmt.Errorf("plan validation failed: %w", err)
	}

	agentID := ""
	if r.Identity != nil {
		agentID = r.Identity.AgentID
	}

	parsed, err := TranslatePlan(plan, jobID, agentID)
	if err != nil {
		return nil, fmt.Errorf("failed to translate plan: %w", err)
	}

	execResult := &ExecutionResult{
		JobID:             jobID,
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

// ExecutePlan validates, translates, and concurrently executes forensic collection requests for a local execution cycle.
func (r *AgentRuntime) ExecutePlan(ctx context.Context, plan *ExecutionPlan) (*ExecutionResult, error) {
	return r.ExecuteJob(ctx, "job-local", plan)
}

// PollAndExecuteNextJob checks the transport for a queued job, executes it, and submits artifacts.
func (r *AgentRuntime) PollAndExecuteNextJob(ctx context.Context) error {
	if r.Transport == nil || r.Identity == nil {
		return nil
	}

	pollResp, err := r.Transport.PollJob(ctx, r.Identity.AgentID)
	if err != nil {
		return fmt.Errorf("failed to poll job: %w", err)
	}

	if pollResp == nil || pollResp.JobID == "" || pollResp.Plan == nil {
		return nil // No pending jobs
	}

	log.Printf("[Agent Runtime] Received dispatched job %s from server", pollResp.JobID)

	planBytes, err := json.Marshal(pollResp.Plan)
	if err != nil {
		return fmt.Errorf("failed to re-marshal plan: %w", err)
	}

	var plan ExecutionPlan
	if err := json.Unmarshal(planBytes, &plan); err != nil {
		return fmt.Errorf("failed to parse received execution plan: %w", err)
	}

	execResult, err := r.ExecuteJob(ctx, pollResp.JobID, &plan)
	if err != nil {
		return fmt.Errorf("execution error on job %s: %w", pollResp.JobID, err)
	}

	// Consolidate non-empty artifacts
	var allArtifacts []collectors.Artifact
	for _, colRes := range execResult.CollectionResults {
		if colRes.Error == nil && len(colRes.Artifacts) > 0 {
			allArtifacts = append(allArtifacts, colRes.Artifacts...)
		}
	}

	log.Printf("[Agent Runtime] Job %s completed with %d artifacts collected. Submitting to server...", pollResp.JobID, len(allArtifacts))

	subReq := transport.ArtifactsSubmissionRequest{
		JobID:     pollResp.JobID,
		AgentID:   r.Identity.AgentID,
		Artifacts: allArtifacts,
	}

	subResp, err := r.Transport.SubmitArtifacts(ctx, subReq)
	if err != nil {
		return fmt.Errorf("failed to submit artifacts for job %s: %w", pollResp.JobID, err)
	}

	log.Printf("[Agent Runtime] Successfully ingested %d artifacts for job %s (status: %s)", subResp.Ingested, pollResp.JobID, subResp.Status)
	return nil
}

// Start begins the agent lifecycle and initializes background polling/heartbeat loops if transport is configured.
func (r *AgentRuntime) Start(ctx context.Context) error {
	hostname := "unknown"
	osType := "unknown"
	arch := "unknown"
	hbSeconds := 5
	if r.Identity != nil {
		hostname = r.Identity.Hostname
		osType = r.Identity.OS
		arch = r.Identity.Arch
		if r.Identity.HeartbeatIntervalSeconds > 0 {
			hbSeconds = r.Identity.HeartbeatIntervalSeconds
		}
	}
	log.Printf("[Agent Runtime] Initialized for %s (%s/%s)", hostname, osType, arch)

	if r.Transport != nil && r.Identity != nil {
		// Start Heartbeat loop
		go func() {
			ticker := time.NewTicker(time.Duration(hbSeconds) * time.Second)
			defer ticker.Stop()

			// Send initial heartbeat immediately
			_, _ = r.Transport.SendHeartbeat(ctx, r.Identity.AgentID, transport.HeartbeatRequest{Status: "online"})

			for {
				select {
				case <-ctx.Done():
					return
				case <-ticker.C:
					_, _ = r.Transport.SendHeartbeat(ctx, r.Identity.AgentID, transport.HeartbeatRequest{Status: "online"})
				}
			}
		}()

		// Start Job Polling loop
		go func() {
			pollTicker := time.NewTicker(2 * time.Second)
			defer pollTicker.Stop()

			for {
				select {
				case <-ctx.Done():
					return
				case <-pollTicker.C:
					if err := r.PollAndExecuteNextJob(ctx); err != nil {
						log.Printf("[Agent Runtime] Error executing polled job: %v", err)
					}
				}
			}
		}()
	}

	return nil
}
