package collectors

import (
	"context"
	"time"
)

// NetworkConnectionInfo represents normalized metadata for an active network socket or connection.
type NetworkConnectionInfo struct {
	Protocol      string `json:"protocol"`       // "tcp", "tcp6", "udp", "udp6"
	LocalAddress  string `json:"local_address"`
	LocalPort     int    `json:"local_port"`
	RemoteAddress string `json:"remote_address"`
	RemotePort    int    `json:"remote_port"`
	State         string `json:"state"`         // "LISTEN", "ESTABLISHED", "TIME_WAIT", "CLOSE_WAIT", "NONE", etc.
	PID           int    `json:"pid"`
}

// NetworkCollector is a read-only forensic collector for active network connections and listening sockets.
type NetworkCollector struct{}

// NewNetworkCollector creates a new NetworkCollector instance.
func NewNetworkCollector() *NetworkCollector {
	return &NetworkCollector{}
}

func (c *NetworkCollector) Name() string {
	return "network-collector"
}

func (c *NetworkCollector) Supports(target string) bool {
	return target == "connections"
}

func (c *NetworkCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}

	conns, err := collectPlatformConnections(ctx)
	if err != nil {
		return nil, err
	}

	artifacts := make([]Artifact, 0, len(conns))
	now := time.Now().UTC()

	for _, conn := range conns {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}

		data := map[string]any{
			"protocol":       conn.Protocol,
			"local_address":  conn.LocalAddress,
			"local_port":     conn.LocalPort,
			"remote_address": conn.RemoteAddress,
			"remote_port":    conn.RemotePort,
			"state":          conn.State,
			"pid":            conn.PID,
		}

		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        "network_connection",
			CollectedAt: now,
			Data:        data,
		})
	}

	return artifacts, nil
}
