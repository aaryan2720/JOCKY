package runtime

import (
	"context"
	"testing"
	"time"

	"github.com/jocky-dfir/jocky/agent/internal/collectors"
	"github.com/jocky-dfir/jocky/agent/internal/registration"
)

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

func TestAgentRuntimeInit(t *testing.T) {
	ctx := context.Background()
	ident := &registration.Identity{
		AgentID:  "agent-test-1",
		Hostname: "test-node",
		OS:       "linux",
		Arch:     "amd64",
	}

	rt := NewRuntime(ident)
	if err := rt.Start(ctx); err != nil {
		t.Fatalf("Failed to start runtime: %v", err)
	}

	if _, err := rt.ExecutePlan(ctx, &ExecutionPlan{
		Version: "1",
		Statements: []ExecutionStatement{
			{Operation: "scan", Target: "processes"},
		},
	}); err != nil {
		t.Fatalf("Failed to execute plan stub: %v", err)
	}
}

func TestAgentRuntimeExecutePlanWithCollectors(t *testing.T) {
	ctx := context.Background()
	ident := &registration.Identity{
		AgentID:  "agent-test-collectors",
		Hostname: "node-dfir",
		OS:       "windows",
		Arch:     "amd64",
	}

	rt := NewRuntime(ident)
	plan := map[string]interface{}{
		"plan_version": "1.0",
		"collectors": []interface{}{
			"autoruns",
			"scheduled_tasks",
			"users",
			"sessions",
		},
	}

	artifacts, err := rt.ExecutePlanArtifacts(ctx, plan)
	if err != nil {
		t.Fatalf("ExecutePlanArtifacts failed: %v", err)
	}

	typeCounts := make(map[string]int)
	for _, art := range artifacts {
		typeCounts[art.Type]++
	}

	for _, expectedType := range []string{"autorun", "scheduled_task", "user", "session"} {
		if typeCounts[expectedType] == 0 {
			t.Logf("Notice: collector produced 0 artifacts of type '%s' on this host environment", expectedType)
		}
	}
}

func TestAgentRuntimeExecutePlanWithPlaceholders(t *testing.T) {
	ctx := context.Background()
	ident := &registration.Identity{
		AgentID:  "agent-test-placeholders",
		Hostname: "node-dfir",
		OS:       "linux",
		Arch:     "amd64",
	}

	rt := NewRuntime(ident)
	rt.Registry.Register(collectors.NewPlaceholderCollector("custom_placeholder"))
	rt.Collectors = rt.Registry.All()

	plan := map[string]interface{}{
		"plan_version": "1.0",
		"collectors": []interface{}{
			"custom_placeholder",
		},
	}

	artifacts, err := rt.ExecutePlanArtifacts(ctx, plan)
	if err != nil {
		t.Fatalf("Placeholder plan execution should not fail: %v", err)
	}

	if len(artifacts) != 1 {
		t.Errorf("Expected 1 placeholder artifact, got %d", len(artifacts))
	}
	for _, a := range artifacts {
		if a.Data["status"] != "placeholder" {
			t.Errorf("Expected placeholder status for %s", a.Type)
		}
	}
}

func TestAgentRuntimeContextCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel context immediately

	ident := &registration.Identity{
		AgentID:  "agent-test-cancel",
		Hostname: "node-dfir",
		OS:       "linux",
		Arch:     "amd64",
	}

	rt := NewRuntime(ident)
	plan := map[string]interface{}{
		"plan_version": "1.0",
		"collectors":   []interface{}{"processes", "connections", "autoruns"},
	}

	_, err := rt.ExecutePlanArtifacts(ctx, plan)
	if err == nil {
		t.Fatalf("Expected cancellation error, got nil")
	}
}

func TestAgentRuntimeTimeoutHandling(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()
	time.Sleep(50 * time.Millisecond) // expire timeout

	ident := &registration.Identity{
		AgentID:  "agent-test-timeout",
		Hostname: "node-dfir",
		OS:       "linux",
		Arch:     "amd64",
	}

	rt := NewRuntime(ident)
	plan := map[string]interface{}{
		"plan_version": "1.0",
		"collectors":   []interface{}{"users"},
	}

	_, err := rt.ExecutePlanArtifacts(ctx, plan)
	if err == nil {
		t.Fatalf("Expected timeout cancellation error, got nil")
	}
}
