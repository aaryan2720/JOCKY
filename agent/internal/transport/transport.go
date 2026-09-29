package transport

import (
	"context"

	"github.com/jocky-dfir/jocky/agent/internal/collectors"
)

// Transport defines the communication contract between the Go Agent and FastAPI Server.
type Transport interface {
	Register(ctx context.Context, token string, hostname string, osType string) (string, error)
	SendHeartbeat(ctx context.Context, agentID string) error
	PollJob(ctx context.Context, agentID string) (map[string]interface{}, error)
	SubmitArtifacts(ctx context.Context, jobID string, agentID string, artifacts []collectors.Artifact) error
}
