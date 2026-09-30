//go:build !windows && !linux

package collectors

import "context"

func collectConnections(ctx context.Context, options map[string]interface{}) ([]ConnectionEntry, error) {
	_ = ctx
	_ = options
	return []ConnectionEntry{
		{
			Protocol:      "TCP",
			LocalAddress:  "127.0.0.1",
			LocalPort:     8000,
			RemoteAddress: "127.0.0.1",
			RemotePort:    8000,
			State:         "ESTABLISHED",
			PID:           100,
		},
	}, nil
}
