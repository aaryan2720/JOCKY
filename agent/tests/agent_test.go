package tests

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	"github.com/jocky-dfir/jocky/agent/internal/collectors"
	"github.com/jocky-dfir/jocky/agent/internal/registration"
	"github.com/jocky-dfir/jocky/agent/internal/runtime"
)

// 1. Valid execution plan parsing
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

// 2. Invalid execution plan (malformed JSON)
func TestMalformedJSONPlan(t *testing.T) {
	badJSON := []byte(`{ "version": "1", "statements": [ invalid ] }`)
	_, err := runtime.ParseExecutionPlan(badJSON)
	if err == nil {
		t.Fatal("Expected error on malformed JSON, got nil")
	}
}

// 3. Unsupported operation rejection
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
	if !strings.Contains(err.Error(), "unsupported operation 'execute'") {
		t.Errorf("Expected error to mention unsupported operation, got: %v", err)
	}
}

// 4. Unsupported target rejection
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
	if !strings.Contains(err.Error(), "unsupported target 'passwords_memory_dump'") {
		t.Errorf("Expected target rejection error, got: %v", err)
	}
}

// 5. Invalid plan version rejection
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
	if !strings.Contains(err.Error(), "unsupported plan version '2'") {
		t.Errorf("Expected version rejection error, got: %v", err)
	}
}

// 6 & 7 & 8. Collector Registration, Resolution, and Unknown Collector
func TestCollectorRegistry(t *testing.T) {
	reg := collectors.NewRegistry()
	placeholder := collectors.NewPlaceholderCollector("processes")
	reg.Register(placeholder)

	// Resolve known collector
	col, found := reg.Resolve("processes")
	if !found {
		t.Fatal("Expected to resolve 'processes' collector")
	}
	if col.Name() != "placeholder-processes" {
		t.Errorf("Expected name 'placeholder-processes', got '%s'", col.Name())
	}

	// Resolve unknown collector
	_, foundUnknown := reg.Resolve("unknown_target")
	if foundUnknown {
		t.Fatal("Expected not found for 'unknown_target'")
	}
}

// 9. Scan -> CollectionRequest
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
	if req.JobID != "job-101" {
		t.Errorf("Expected JobID 'job-101', got '%s'", req.JobID)
	}
	if len(req.Conditions) != 1 || req.Conditions[0].Field != "signed" {
		t.Errorf("Expected condition field 'signed', got: %+v", req.Conditions)
	}
}

// 10. Collect multiple targets -> multiple CollectionRequests
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
	expectedTargets := []string{"autoruns", "scheduled_tasks", "services"}
	for i, target := range expectedTargets {
		if parsed.CollectionRequests[i].Target != target {
			t.Errorf("At index %d, expected target '%s', got '%s'", i, target, parsed.CollectionRequests[i].Target)
		}
	}
}

// 11. Hash -> HashRequest representation
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
	hashReq := parsed.HashRequests[0]
	if hashReq.Path != "%TEMP%" || hashReq.CheckAgainst != "reputation" {
		t.Errorf("Unexpected hash request content: %+v", hashReq)
	}
}

// 12. Flag -> FlagInstruction
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
	flagInst := parsed.FlagInstructions[0]
	if flagInst.Severity != "critical" || flagInst.Condition.Field != "signed" {
		t.Errorf("Unexpected flag instruction content: %+v", flagInst)
	}
}

// 13. Report -> ReportInstruction
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
	if parsed.ReportInstructions[0].Destination != "server" {
		t.Errorf("Expected destination 'server', got '%s'", parsed.ReportInstructions[0].Destination)
	}
}

// 14. Context cancellation
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

// 15. Placeholder collectors explicitly return ErrNotImplemented (No fake data!)
func TestPlaceholderCollectorsReturnErrNotImplemented(t *testing.T) {
	reg := collectors.NewDefaultRegistry()
	ctx := context.Background()

	for _, target := range collectors.DefaultTargets {
		col, found := reg.Resolve(target)
		if !found {
			t.Fatalf("Target '%s' not found in default registry", target)
		}

		artifacts, err := col.Collect(ctx, collectors.CollectionRequest{Target: target})
		if err == nil {
			t.Fatalf("Target '%s' was expected to return error, but got nil", target)
		}
		if !errors.Is(err, collectors.ErrNotImplemented) {
			t.Fatalf("Target '%s' expected ErrNotImplemented, got: %v", target, err)
		}
		if len(artifacts) != 0 {
			t.Fatalf("Target '%s' must NEVER return fake artifacts during placeholder phase, got %d", target, len(artifacts))
		}
	}
}

// 16. End-to-end plan -> runtime instruction generation & execution cycle
func TestEndToEndPlanExecution(t *testing.T) {
	planJSON := []byte(`{
		"version": "1",
		"statements": [
			{
				"operation": "scan",
				"target": "processes",
				"where": {
					"operator": "and",
					"conditions": [
						{
							"field": "signed",
							"operator": "eq",
							"value": false
						},
						{
							"field": "network_connections",
							"operator": "gt",
							"value": 0
						}
					]
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
		t.Fatalf("Failed to parse plan: %v", err)
	}

	ident := &registration.Identity{
		AgentID:  "agent-win-01",
		Hostname: "WIN-ENDPOINT-01",
		OS:       "windows",
		Arch:     "amd64",
	}
	rt := runtime.NewRuntime(ident)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	result, err := rt.ExecutePlan(ctx, plan)
	if err != nil {
		t.Fatalf("ExecutePlan failed: %v", err)
	}

	if result.PlanVersion != "1" {
		t.Errorf("Expected PlanVersion '1', got '%s'", result.PlanVersion)
	}

	// Expect 3 collection results (1 from scan + 2 from collect autoruns, scheduled_tasks)
	if len(result.CollectionResults) != 3 {
		t.Fatalf("Expected 3 collection results, got %d", len(result.CollectionResults))
	}

	for _, colRes := range result.CollectionResults {
		if !errors.Is(colRes.Error, collectors.ErrNotImplemented) {
			t.Errorf("Expected target %s to return ErrNotImplemented, got: %v", colRes.Target, colRes.Error)
		}
	}

	if len(result.ParsedPlan.HashRequests) != 1 {
		t.Errorf("Expected 1 hash request, got %d", len(result.ParsedPlan.HashRequests))
	}
	if len(result.ParsedPlan.FlagInstructions) != 1 {
		t.Errorf("Expected 1 flag instruction, got %d", len(result.ParsedPlan.FlagInstructions))
	}
	if len(result.ParsedPlan.ReportInstructions) != 1 {
		t.Errorf("Expected 1 report instruction, got %d", len(result.ParsedPlan.ReportInstructions))
	}
}

// Enrollment test from Phase 0
func TestAgentEnrollment(t *testing.T) {
	ctx := context.Background()
	ident, err := registration.Enroll(ctx, "http://localhost:8000", "test-token")
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
