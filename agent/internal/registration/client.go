package registration

import (
	"context"
	"fmt"
	"os"
	"runtime"
)

// Identity represents the enrolled agent's local state.
type Identity struct {
	AgentID  string `json:"agent_id"`
	Hostname string `json:"hostname"`
	OS       string `json:"os"`
	Arch     string `json:"arch"`
}

// Enroll performs initial handshake and discovery.
func Enroll(ctx context.Context, serverURL string, token string) (*Identity, error) {
	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown-host"
	}

	return &Identity{
		AgentID:  fmt.Sprintf("agent-%s-%s", hostname, runtime.GOOS),
		Hostname: hostname,
		OS:       runtime.GOOS,
		Arch:     runtime.GOARCH,
	}, nil
}
