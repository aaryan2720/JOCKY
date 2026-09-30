package tests

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/jocky-dfir/jocky/agent/internal/collectors"
	"github.com/jocky-dfir/jocky/agent/internal/registration"
	"github.com/jocky-dfir/jocky/agent/internal/runtime"
	"github.com/jocky-dfir/jocky/agent/internal/transport"
)

// 1. ProcessCollector Unit & Structure Test
func TestProcessCollector(t *testing.T) {
	col := collectors.NewProcessCollector()
	if col.Name() != "process-collector" {
		t.Errorf("Expected name 'process-collector', got '%s'", col.Name())
	}
	if !col.Supports("processes") {
		t.Error("Expected ProcessCollector to support 'processes'")
	}
	if col.Supports("connections") {
		t.Error("ProcessCollector should not support 'connections'")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	artifacts, err := col.Collect(ctx, collectors.CollectionRequest{
		Target:  "processes",
		JobID:   "job-test-proc",
		AgentID: "agent-test-01",
	})
	if err != nil {
		t.Fatalf("Process collection failed: %v", err)
	}

	if len(artifacts) == 0 {
		t.Fatal("Expected at least one running process on host, got 0")
	}

	// Verify process artifact schema
	first := artifacts[0]
	if first.Type != "process" {
		t.Errorf("Expected artifact type 'process', got '%s'", first.Type)
	}
	if first.JobID != "job-test-proc" || first.AgentID != "agent-test-01" {
		t.Errorf("JobID/AgentID not preserved: %+v", first)
	}

	data := first.Data
	if _, ok := data["pid"]; !ok {
		t.Error("Missing 'pid' field in process data")
	}
	if _, ok := data["name"]; !ok {
		t.Error("Missing 'name' field in process data")
	}
	if _, ok := data["signature_status"]; !ok {
		t.Error("Missing 'signature_status' field in process data")
	}
}

// 2. NetworkCollector Unit & Structure Test
func TestNetworkCollector(t *testing.T) {
	col := collectors.NewNetworkCollector()
	if col.Name() != "network-collector" {
		t.Errorf("Expected name 'network-collector', got '%s'", col.Name())
	}
	if !col.Supports("connections") {
		t.Error("Expected NetworkCollector to support 'connections'")
	}
	if col.Supports("processes") {
		t.Error("NetworkCollector should not support 'processes'")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	artifacts, err := col.Collect(ctx, collectors.CollectionRequest{
		Target:  "connections",
		JobID:   "job-test-net",
		AgentID: "agent-test-01",
	})
	if err != nil {
		t.Fatalf("Network collection failed: %v", err)
	}

	// On any active machine, network sockets exist
	if len(artifacts) == 0 {
		t.Log("Note: 0 network connections returned on host (idle test environment)")
	} else {
		first := artifacts[0]
		if first.Type != "network_connection" {
			t.Errorf("Expected artifact type 'network_connection', got '%s'", first.Type)
		}
		if _, ok := first.Data["protocol"]; !ok {
			t.Error("Missing 'protocol' in network artifact data")
		}
		if _, ok := first.Data["local_address"]; !ok {
			t.Error("Missing 'local_address' in network artifact data")
		}
		if _, ok := first.Data["state"]; !ok {
			t.Error("Missing 'state' in network artifact data")
		}
	}
}

// 3. Registry Resolution Test (Real vs Placeholders)
func TestDefaultRegistryResolution(t *testing.T) {
	reg := collectors.NewDefaultRegistry()

	// Real Process Collector
	procCol, found := reg.Resolve("processes")
	if !found {
		t.Fatal("Failed to resolve 'processes' collector")
	}
	if procCol.Name() != "process-collector" {
		t.Errorf("Expected 'process-collector', got '%s'", procCol.Name())
	}

	// Real Network Collector
	netCol, found := reg.Resolve("connections")
	if !found {
		t.Fatal("Failed to resolve 'connections' collector")
	}
	if netCol.Name() != "network-collector" {
		t.Errorf("Expected 'network-collector', got '%s'", netCol.Name())
	}

	// Placeholders
	for _, target := range collectors.PlaceholderTargets {
		col, found := reg.Resolve(target)
		if !found {
			t.Errorf("Failed to resolve placeholder for '%s'", target)
		}
		if !strings.HasPrefix(col.Name(), "placeholder-") {
			t.Errorf("Expected placeholder name for '%s', got '%s'", target, col.Name())
		}
	}
}

// 4. Placeholder collectors explicitly return ErrNotImplemented (No fake data!)
func TestPlaceholderTargetsReturnErrNotImplemented(t *testing.T) {
	reg := collectors.NewDefaultRegistry()
	ctx := context.Background()

	for _, target := range collectors.PlaceholderTargets {
		col, found := reg.Resolve(target)
		if !found {
			t.Fatalf("Target '%s' not found in registry", target)
		}

		artifacts, err := col.Collect(ctx, collectors.CollectionRequest{Target: target})
		if err == nil {
			t.Fatalf("Target '%s' was expected to return error, but got nil", target)
		}
		if !errors.Is(err, collectors.ErrNotImplemented) {
			t.Fatalf("Target '%s' expected ErrNotImplemented, got: %v", target, err)
		}
		if len(artifacts) != 0 {
			t.Fatalf("Target '%s' must NEVER return fake artifacts, got %d", target, len(artifacts))
		}
	}
}

// 5. Valid execution plan parsing
func TestValidExecutionPlanParsing(t *testing.T) {
	planJSON := []byte(`{
		"version": "1",
		"statements": [
			{
				"operation": "scan",
				"target": "processes",
				"where": {
					"field": "signed",
					"operator": "eq",
					"value": false
				}
			},
			{
				"operation": "collect",
				"targets": ["autoruns", "scheduled_tasks"]
			},
			{
				"operation": "hash",
				"target": "files",
				"path": "%TEMP%",
				"check_against": "reputation"
			},
			{
				"operation": "flag",
				"condition": {
					"field": "signed",
					"operator": "eq",
					"value": false
				},
				"severity": "high"
			},
			{
				"operation": "report",
				"destination": "server"
			}
		]
	}`)

	plan, err := runtime.ParseExecutionPlan(planJSON)
	if err != nil {
		t.Fatalf("Failed to parse valid execution plan: %v", err)
	}

	if plan.Version != "1" {
		t.Errorf("Expected version '1', got '%s'", plan.Version)
	}
	if len(plan.Statements) != 5 {
		t.Fatalf("Expected 5 statements, got %d", len(plan.Statements))
	}

	if err := runtime.ValidatePlan(plan); err != nil {
		t.Fatalf("Validation failed on valid plan: %v", err)
	}
}

// 6. Invalid execution plan (malformed JSON)
func TestMalformedJSONPlan(t *testing.T) {
	badJSON := []byte(`{ "version": "1", "statements": [ invalid ] }`)
	_, err := runtime.ParseExecutionPlan(badJSON)
	if err == nil {
		t.Fatal("Expected error on malformed JSON, got nil")
	}
}

// 7. Unsupported operation rejection
func TestUnsupportedOperationRejection(t *testing.T) {
	plan := &runtime.ExecutionPlan{
		Version: "1",
		Statements: []runtime.ExecutionStatement{
			{
				Operation: "execute",
				Path:      "cmd.exe",
			},
		},
	}

	err := runtime.ValidatePlan(plan)
	if err == nil {
		t.Fatal("Expected validation error for 'execute' operation, got nil")
	}

	var valErr *runtime.PlanValidationError
	if !errors.As(err, &valErr) {
		t.Errorf("Expected error of type PlanValidationError, got: %T", err)
	}
}

// 8. Unsupported target rejection
func TestUnsupportedTargetRejection(t *testing.T) {
	plan := &runtime.ExecutionPlan{
		Version: "1",
		Statements: []runtime.ExecutionStatement{
			{
				Operation: "scan",
				Target:    "passwords_memory_dump",
			},
		},
	}

	err := runtime.ValidatePlan(plan)
	if err == nil {
		t.Fatal("Expected validation error for unsupported target, got nil")
	}
}

// 9. Invalid plan version rejection
func TestInvalidPlanVersionRejection(t *testing.T) {
	plan := &runtime.ExecutionPlan{
		Version: "2",
		Statements: []runtime.ExecutionStatement{
			{
				Operation: "scan",
				Target:    "processes",
			},
		},
	}

	err := runtime.ValidatePlan(plan)
	if err == nil {
		t.Fatal("Expected validation error for version '2', got nil")
	}
}

// 10. Scan -> CollectionRequest
func TestTranslateScanToCollectionRequest(t *testing.T) {
	plan := &runtime.ExecutionPlan{
		Version: "1",
		Statements: []runtime.ExecutionStatement{
			{
				Operation: "scan",
				Target:    "processes",
				Where: &runtime.ConditionClause{
					Field:    "signed",
					Operator: "eq",
					Value:    false,
				},
			},
		},
	}

	parsed, err := runtime.TranslatePlan(plan, "job-101", "agent-01")
	if err != nil {
		t.Fatalf("TranslatePlan failed: %v", err)
	}

	if len(parsed.CollectionRequests) != 1 {
		t.Fatalf("Expected 1 collection request, got %d", len(parsed.CollectionRequests))
	}
	req := parsed.CollectionRequests[0]
	if req.Target != "processes" {
		t.Errorf("Expected target 'processes', got '%s'", req.Target)
	}
}

// 11. Collect multiple targets -> multiple CollectionRequests
func TestTranslateCollectMultipleTargets(t *testing.T) {
	plan := &runtime.ExecutionPlan{
		Version: "1",
		Statements: []runtime.ExecutionStatement{
			{
				Operation: "collect",
				Targets:   []string{"autoruns", "scheduled_tasks", "services"},
			},
		},
	}

	parsed, err := runtime.TranslatePlan(plan, "job-102", "agent-01")
	if err != nil {
		t.Fatalf("TranslatePlan failed: %v", err)
	}

	if len(parsed.CollectionRequests) != 3 {
		t.Fatalf("Expected 3 collection requests, got %d", len(parsed.CollectionRequests))
	}
}

// 12. Hash -> HashRequest representation
func TestTranslateHashRequest(t *testing.T) {
	plan := &runtime.ExecutionPlan{
		Version: "1",
		Statements: []runtime.ExecutionStatement{
			{
				Operation:    "hash",
				Target:       "files",
				Path:         "%TEMP%",
				CheckAgainst: "reputation",
			},
		},
	}

	parsed, err := runtime.TranslatePlan(plan, "job-103", "agent-01")
	if err != nil {
		t.Fatalf("TranslatePlan failed: %v", err)
	}

	if len(parsed.HashRequests) != 1 {
		t.Fatalf("Expected 1 hash request, got %d", len(parsed.HashRequests))
	}
}

// 13. Flag -> FlagInstruction
func TestTranslateFlagInstruction(t *testing.T) {
	plan := &runtime.ExecutionPlan{
		Version: "1",
		Statements: []runtime.ExecutionStatement{
			{
				Operation: "flag",
				Condition: &runtime.ConditionClause{
					Field:    "signed",
					Operator: "eq",
					Value:    false,
				},
				Severity: "critical",
			},
		},
	}

	parsed, err := runtime.TranslatePlan(plan, "job-104", "agent-01")
	if err != nil {
		t.Fatalf("TranslatePlan failed: %v", err)
	}

	if len(parsed.FlagInstructions) != 1 {
		t.Fatalf("Expected 1 flag instruction, got %d", len(parsed.FlagInstructions))
	}
}

// 14. Report -> ReportInstruction
func TestTranslateReportInstruction(t *testing.T) {
	plan := &runtime.ExecutionPlan{
		Version: "1",
		Statements: []runtime.ExecutionStatement{
			{
				Operation:   "report",
				Destination: "server",
			},
		},
	}

	parsed, err := runtime.TranslatePlan(plan, "job-105", "agent-01")
	if err != nil {
		t.Fatalf("TranslatePlan failed: %v", err)
	}

	if len(parsed.ReportInstructions) != 1 {
		t.Fatalf("Expected 1 report instruction, got %d", len(parsed.ReportInstructions))
	}
}

// 15. Context cancellation
func TestContextCancellationDuringExecution(t *testing.T) {
	ident := &registration.Identity{
		AgentID:  "agent-test-01",
		Hostname: "test-node",
		OS:       "linux",
		Arch:     "amd64",
	}
	rt := runtime.NewRuntime(ident)

	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel context immediately

	plan := &runtime.ExecutionPlan{
		Version: "1",
		Statements: []runtime.ExecutionStatement{
			{
				Operation: "scan",
				Target:    "processes",
			},
		},
	}

	res, err := rt.ExecutePlan(ctx, plan)
	if err != nil {
		t.Fatalf("ExecutePlan error: %v", err)
	}

	if len(res.CollectionResults) != 1 {
		t.Fatalf("Expected 1 collection result, got %d", len(res.CollectionResults))
	}
	if !errors.Is(res.CollectionResults[0].Error, context.Canceled) {
		t.Errorf("Expected context.Canceled error, got: %v", res.CollectionResults[0].Error)
	}
}

// 16. End-to-end plan -> real Process & Network collection
func TestEndToEndPlanWithRealCollectors(t *testing.T) {
	planJSON := []byte(`{
		"version": "1",
		"statements": [
			{
				"operation": "scan",
				"target": "processes"
			},
			{
				"operation": "scan",
				"target": "connections"
			},
			{
				"operation": "collect",
				"targets": ["autoruns"]
			}
		]
	}`)

	plan, err := runtime.ParseExecutionPlan(planJSON)
	if err != nil {
		t.Fatalf("Failed to parse plan: %v", err)
	}

	ident := &registration.Identity{
		AgentID:  "agent-win-01",
		Hostname: "WIN-ENDPOINT-01",
		OS:       "windows",
		Arch:     "amd64",
	}
	rt := runtime.NewRuntime(ident)

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	result, err := rt.ExecutePlan(ctx, plan)
	if err != nil {
		t.Fatalf("ExecutePlan failed: %v", err)
	}

	if len(result.CollectionResults) != 3 {
		t.Fatalf("Expected 3 collection results, got %d", len(result.CollectionResults))
	}

	// Map results by target
	resMap := make(map[string]runtime.CollectionResult)
	for _, cr := range result.CollectionResults {
		resMap[cr.Target] = cr
	}

	// 1. Process Collector should succeed and return real artifacts
	procRes, ok := resMap["processes"]
	if !ok {
		t.Fatal("Missing 'processes' in results")
	}
	if procRes.Error != nil {
		t.Fatalf("Process collection returned unexpected error: %v", procRes.Error)
	}
	if len(procRes.Artifacts) == 0 {
		t.Error("Expected real process artifacts from host, got 0")
	}

	// 2. Network Collector should succeed
	netRes, ok := resMap["connections"]
	if !ok {
		t.Fatal("Missing 'connections' in results")
	}
	if netRes.Error != nil {
		t.Fatalf("Network collection returned unexpected error: %v", netRes.Error)
	}

	// 3. Autoruns placeholder should return ErrNotImplemented
	autorunRes, ok := resMap["autoruns"]
	if !ok {
		t.Fatal("Missing 'autoruns' in results")
	}
	if !errors.Is(autorunRes.Error, collectors.ErrNotImplemented) {
		t.Errorf("Expected autoruns placeholder to return ErrNotImplemented, got: %v", autorunRes.Error)
	}
}

// 17. Enrollment fallback test
func TestAgentEnrollment(t *testing.T) {
	ctx := context.Background()
	ident, err := registration.Enroll(ctx, "", "test-token")
	if err != nil {
		t.Fatalf("Enroll failed: %v", err)
	}

	if ident.AgentID == "" {
		t.Errorf("Expected non-empty AgentID")
	}
	if ident.OS == "" {
		t.Errorf("Expected non-empty OS")
	}
}

// 18. HTTPTransport Mock Server Test (Register, Heartbeat, PollJob, SubmitArtifacts)
func TestHTTPTransportMockServer(t *testing.T) {
	// Setup mock HTTP server mimicking FastAPI routes
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.Method == http.MethodPost && r.URL.Path == "/api/v1/agents/register":
			var req transport.RegisterRequest
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				http.Error(w, err.Error(), http.StatusBadRequest)
				return
			}
			w.WriteHeader(http.StatusCreated)
			_ = json.NewEncoder(w).Encode(transport.RegisterResponse{
				AgentID:                  "agent-mock-host-win",
				Status:                   "enrolled",
				HeartbeatIntervalSeconds: 3,
			})

		case r.Method == http.MethodPost && strings.HasPrefix(r.URL.Path, "/api/v1/agents/") && strings.HasSuffix(r.URL.Path, "/heartbeat"):
			w.WriteHeader(http.StatusOK)
			_ = json.NewEncoder(w).Encode(transport.HeartbeatResponse{
				Status:    "ok",
				Timestamp: time.Now().UTC().Format(time.RFC3339),
			})

		case r.Method == http.MethodGet && strings.HasSuffix(r.URL.Path, "/jobs/poll"):
			w.WriteHeader(http.StatusOK)
			_ = json.NewEncoder(w).Encode(transport.JobPollResponse{
				JobID: "job-http-101",
				Plan: map[string]interface{}{
					"version": "1",
					"statements": []interface{}{
						map[string]interface{}{
							"operation": "scan",
							"target":    "processes",
						},
					},
				},
			})

		case r.Method == http.MethodPost && r.URL.Path == "/api/v1/artifacts":
			var req transport.ArtifactsSubmissionRequest
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				http.Error(w, err.Error(), http.StatusBadRequest)
				return
			}
			w.WriteHeader(http.StatusCreated)
			_ = json.NewEncoder(w).Encode(transport.ArtifactsSubmissionResponse{
				Status:   "ok",
				Ingested: len(req.Artifacts),
			})

		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	tr := transport.NewHTTPTransport(server.URL, "test-auth-token")

	// 1. Test Register
	regResp, err := tr.Register(ctx, transport.RegisterRequest{
		Token:        "test-token",
		Hostname:     "mock-host",
		OS:           "windows",
		Arch:         "amd64",
		AgentVersion: "0.1.0",
	})
	if err != nil {
		t.Fatalf("Register failed: %v", err)
	}
	if regResp.AgentID != "agent-mock-host-win" {
		t.Errorf("Unexpected AgentID: %s", regResp.AgentID)
	}
	if regResp.HeartbeatIntervalSeconds != 3 {
		t.Errorf("Unexpected heartbeat interval: %d", regResp.HeartbeatIntervalSeconds)
	}

	// 2. Test Heartbeat
	hbResp, err := tr.SendHeartbeat(ctx, regResp.AgentID, transport.HeartbeatRequest{Status: "online"})
	if err != nil {
		t.Fatalf("SendHeartbeat failed: %v", err)
	}
	if hbResp.Status != "ok" {
		t.Errorf("Unexpected heartbeat status: %s", hbResp.Status)
	}

	// 3. Test PollJob
	pollResp, err := tr.PollJob(ctx, regResp.AgentID)
	if err != nil {
		t.Fatalf("PollJob failed: %v", err)
	}
	if pollResp.JobID != "job-http-101" {
		t.Errorf("Unexpected job ID: %s", pollResp.JobID)
	}
	if pollResp.Plan == nil {
		t.Fatal("Expected non-nil plan in poll response")
	}

	// 4. Test SubmitArtifacts
	subResp, err := tr.SubmitArtifacts(ctx, transport.ArtifactsSubmissionRequest{
		JobID:   pollResp.JobID,
		AgentID: regResp.AgentID,
		Artifacts: []collectors.Artifact{
			{
				ID:   "art-01",
				Type: "process",
				Data: map[string]interface{}{"pid": 1234},
			},
		},
	})
	if err != nil {
		t.Fatalf("SubmitArtifacts failed: %v", err)
	}
	if subResp.Ingested != 1 {
		t.Errorf("Expected 1 ingested artifact, got %d", subResp.Ingested)
	}
}

// 19. HTTPTransport Server Error Handling Test
func TestHTTPTransportServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	}))
	defer server.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	tr := transport.NewHTTPTransport(server.URL, "token")

	_, err := tr.Register(ctx, transport.RegisterRequest{})
	if err == nil {
		t.Error("Expected error from 500 server response, got nil")
	}

	_, err = tr.SendHeartbeat(ctx, "agent-01", transport.HeartbeatRequest{})
	if err == nil {
		t.Error("Expected error on heartbeat 500, got nil")
	}

	_, err = tr.PollJob(ctx, "agent-01")
	if err == nil {
		t.Error("Expected error on poll 500, got nil")
	}

	_, err = tr.SubmitArtifacts(ctx, transport.ArtifactsSubmissionRequest{})
	if err == nil {
		t.Error("Expected error on submit artifacts 500, got nil")
	}
}

// 20. End-to-End Poll, Execute, and Ingest Cycle with Mock Server and Real OS Collectors
func TestPollAndExecuteNextJobEndToEnd(t *testing.T) {
	var ingestedArtifacts []collectors.Artifact
	jobServed := false

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case strings.HasSuffix(r.URL.Path, "/jobs/poll"):
			if !jobServed {
				jobServed = true
				_ = json.NewEncoder(w).Encode(transport.JobPollResponse{
					JobID: "job-e2e-dispatch-999",
					Plan: map[string]interface{}{
						"version": "1",
						"statements": []interface{}{
							map[string]interface{}{
								"operation": "scan",
								"target":    "processes",
							},
							map[string]interface{}{
								"operation": "scan",
								"target":    "connections",
							},
						},
					},
				})
			} else {
				w.WriteHeader(http.StatusNoContent)
			}

		case r.URL.Path == "/api/v1/artifacts":
			var req transport.ArtifactsSubmissionRequest
			_ = json.NewDecoder(r.Body).Decode(&req)
			ingestedArtifacts = append(ingestedArtifacts, req.Artifacts...)
			w.WriteHeader(http.StatusCreated)
			_ = json.NewEncoder(w).Encode(transport.ArtifactsSubmissionResponse{
				Status:   "ok",
				Ingested: len(req.Artifacts),
			})
		}
	}))
	defer server.Close()

	ident := &registration.Identity{
		AgentID:                  "agent-e2e-tester",
		Hostname:                 "TEST-HOST",
		OS:                       "windows",
		Arch:                     "amd64",
		HeartbeatIntervalSeconds: 5,
	}

	rt := runtime.NewRuntime(ident)
	rt.Transport = transport.NewHTTPTransport(server.URL, "token")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Execute single poll & run cycle
	err := rt.PollAndExecuteNextJob(ctx)
	if err != nil {
		t.Fatalf("PollAndExecuteNextJob failed: %v", err)
	}

	if len(ingestedArtifacts) == 0 {
		t.Fatal("Expected live artifacts to be collected and submitted to the server")
	}

	// Verify we collected process artifacts
	hasProcess := false
	for _, art := range ingestedArtifacts {
		if art.Type == "process" {
			hasProcess = true
			break
		}
	}
	if !hasProcess {
		t.Error("Expected at least one 'process' artifact in submitted artifacts")
	}
}
