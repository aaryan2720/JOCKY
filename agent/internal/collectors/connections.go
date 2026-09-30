package collectors

import (
	"context"
	"net"
	"strconv"
	"strings"
	"time"
)

// ConnectionEntry represents a normalized network socket/connection.
type ConnectionEntry struct {
	Protocol      string `json:"protocol"`
	LocalAddress  string `json:"local_address"`
	LocalPort     int    `json:"local_port"`
	RemoteAddress string `json:"remote_address"`
	RemotePort    int    `json:"remote_port"`
	State         string `json:"state"`
	PID           int    `json:"pid"`
}

// ConnectionCollector collects active TCP/UDP sockets and network connections.
type ConnectionCollector struct{}

// NewConnectionCollector creates a new instance of ConnectionCollector.
func NewConnectionCollector() *ConnectionCollector {
	return &ConnectionCollector{}
}

func (c *ConnectionCollector) Name() string {
	return "connections"
}

func (c *ConnectionCollector) Supports(target string) bool {
	return target == "connections" || target == "network_connections"
}

func (c *ConnectionCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	entries, err := collectConnections(ctx, request.Parameters)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, conn := range entries {
		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        "network_connection",
			CollectedAt: now,
			Data: map[string]interface{}{
				"protocol":       conn.Protocol,
				"local_address":  conn.LocalAddress,
				"local_port":     conn.LocalPort,
				"remote_address": conn.RemoteAddress,
				"dest_ip":        conn.RemoteAddress,
				"remote_port":    conn.RemotePort,
				"dest_port":      conn.RemotePort,
				"state":          conn.State,
				"pid":            conn.PID,
			},
		})
	}

	return artifacts, nil
}

// ParseLinuxNetstatOutput parses Linux ss or netstat output into ConnectionEntry.
func ParseLinuxNetstatOutput(output string) []ConnectionEntry {
	lines := strings.Split(output, "\n")
	var entries []ConnectionEntry

	for _, line := range lines {
		line = strings.TrimSpace(line)
		fields := strings.Fields(line)
		if len(fields) < 4 {
			continue
		}

		proto := strings.ToUpper(fields[0])
		if !strings.HasPrefix(proto, "TCP") && !strings.HasPrefix(proto, "UDP") {
			continue
		}

		var localField, remoteField, stateField string

		// If standard netstat: proto, recv-q, send-q, local, remote, state
		if len(fields) >= 6 && (fields[1] == "0" || strings.HasPrefix(fields[1], "0")) && (fields[2] == "0" || strings.HasPrefix(fields[2], "0")) {
			localField = fields[3]
			remoteField = fields[4]
			stateField = fields[5]
		} else {
			// Find columns with host:port
			for _, f := range fields[1:] {
				if strings.Contains(f, ":") {
					if localField == "" {
						localField = f
					} else if remoteField == "" {
						remoteField = f
					}
				}
			}
			if len(fields) >= 4 {
				stateField = fields[len(fields)-1]
			}
		}

		localAddr, localPortStr, _ := net.SplitHostPort(localField)
		localPort, _ := strconv.Atoi(localPortStr)

		var remoteAddr string
		var remotePort int
		if remoteField != "" && remoteField != "*:*" && remoteField != "0.0.0.0:*" {
			var remotePortStr string
			remoteAddr, remotePortStr, _ = net.SplitHostPort(remoteField)
			remotePort, _ = strconv.Atoi(remotePortStr)
		}

		entries = append(entries, ConnectionEntry{
			Protocol:      proto,
			LocalAddress:  localAddr,
			LocalPort:     localPort,
			RemoteAddress: remoteAddr,
			RemotePort:    remotePort,
			State:         stateField,
			PID:           0,
		})
	}

	return entries
}
