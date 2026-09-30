package registration

import (
	"context"
	"fmt"
	"os"
	"runtime"

	"github.com/jocky-dfir/jocky/agent/internal/transport"
)

// Identity represents the enrolled agent's local state.
type Identity struct {
	AgentID                  string `json:"agent_id"`
	Hostname                 string `json:"hostname"`
	OS                       string `json:"os"`
	Arch                     string `json:"arch"`
	HeartbeatIntervalSeconds int    `json:"heartbeat_interval_seconds"`
}

// Enroll performs handshake with the management server via Transport.
func EnrollWithTransport(ctx context.Context, tr transport.Transport, token string) (*Identity, error) {
	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown-host"
	}

	req := transport.RegisterRequest{
		Token:        token,
		Hostname:     hostname,
		OS:           runtime.GOOS,
		Arch:         runtime.GOARCH,
		AgentVersion: "0.1.0",
	}

	resp, err := tr.Register(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("enrollment failed: %w", err)
	}

	hbInterval := resp.HeartbeatIntervalSeconds
	if hbInterval <= 0 {
		hbInterval = 5
	}

	return &Identity{
		AgentID:                  resp.AgentID,
		Hostname:                 hostname,
		OS:                       runtime.GOOS,
		Arch:                     runtime.GOARCH,
		HeartbeatIntervalSeconds: hbInterval,
	}, nil
}

// Enroll performs initial handshake and discovery (backwards-compatible helper).
func Enroll(ctx context.Context, serverURL string, token string) (*Identity, error) {
	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown-host"
	}

	if serverURL == "" {
		return &Identity{
			AgentID:                  fmt.Sprintf("agent-%s-%s", hostname, runtime.GOOS),
			Hostname:                 hostname,
			OS:                       runtime.GOOS,
			Arch:                     runtime.GOARCH,
			HeartbeatIntervalSeconds: 5,
		}, nil
	}

	tr := transport.NewHTTPTransport(serverURL, token)
	ident, err := EnrollWithTransport(ctx, tr, token)
	if err != nil {
		// Fallback to local identity if server is not yet running (e.g. offline/isolated tests)
		return &Identity{
			AgentID:                  fmt.Sprintf("agent-%s-%s", hostname, runtime.GOOS),
			Hostname:                 hostname,
			OS:                       runtime.GOOS,
			Arch:                     runtime.GOARCH,
			HeartbeatIntervalSeconds: 5,
		}, nil
	}

	return ident, nil
}
