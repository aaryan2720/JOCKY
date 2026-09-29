package tests

import (
	"context"
	"testing"

	"github.com/jocky-dfir/jocky/agent/internal/registration"
	"github.com/jocky-dfir/jocky/agent/internal/runtime"
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

	rt := runtime.NewRuntime(ident)
	if err := rt.Start(ctx); err != nil {
		t.Fatalf("Failed to start runtime: %v", err)
	}

	if err := rt.ExecutePlan(ctx, map[string]interface{}{"plan_version": "1.0"}); err != nil {
		t.Fatalf("Failed to execute plan stub: %v", err)
	}
}
