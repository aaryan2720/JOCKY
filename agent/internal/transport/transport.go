package transport

import (
	"context"

	"github.com/jocky-dfir/jocky/agent/internal/collectors"
)

// RegisterRequest defines the payload sent during agent enrollment.
type RegisterRequest struct {
	Token        string `json:"token"`
	Hostname     string `json:"hostname"`
	OS           string `json:"os"`
	Arch         string `json:"arch"`
	AgentVersion string `json:"agent_version"`
}

// RegisterResponse defines the enrollment response from the server.
type RegisterResponse struct {
	AgentID                  string `json:"agent_id"`
	Status                   string `json:"status"`
	HeartbeatIntervalSeconds int    `json:"heartbeat_interval_seconds"`
}

// HeartbeatRequest defines the payload for periodic presence signals.
type HeartbeatRequest struct {
	Status string `json:"status"`
}

// HeartbeatResponse defines the server confirmation of a heartbeat.
type HeartbeatResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
}

// JobPollResponse contains any queued job and execution plan for the agent.
type JobPollResponse struct {
	JobID string                 `json:"job_id,omitempty"`
	Plan  map[string]interface{} `json:"plan,omitempty"`
}

// ArtifactsSubmissionRequest defines the payload for batch artifact ingestion.
type ArtifactsSubmissionRequest struct {
	JobID     string                `json:"job_id"`
	AgentID   string                `json:"agent_id"`
	Artifacts []collectors.Artifact `json:"artifacts"`
}

// ArtifactsSubmissionResponse defines the ingestion receipt.
type ArtifactsSubmissionResponse struct {
	Status   string `json:"status"`
	Ingested int    `json:"ingested"`
}

// Transport defines the communication contract between the Go Agent and FastAPI Server.
type Transport interface {
	Register(ctx context.Context, req RegisterRequest) (*RegisterResponse, error)
	SendHeartbeat(ctx context.Context, agentID string, req HeartbeatRequest) (*HeartbeatResponse, error)
	PollJob(ctx context.Context, agentID string) (*JobPollResponse, error)
	SubmitArtifacts(ctx context.Context, req ArtifactsSubmissionRequest) (*ArtifactsSubmissionResponse, error)
}
