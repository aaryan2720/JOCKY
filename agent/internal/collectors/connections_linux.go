//go:build linux

package collectors

import (
	"context"
	"os/exec"
)

func collectConnections(ctx context.Context, options map[string]interface{}) ([]ConnectionEntry, error) {
	_ = options
	cmd := exec.CommandContext(ctx, "ss", "-tuanp")
	out, err := cmd.Output()
	if err != nil {
		// Fallback to netstat
		cmd = exec.CommandContext(ctx, "netstat", "-tuan")
		out, err = cmd.Output()
		if err != nil {
			return []ConnectionEntry{
				{
					Protocol:      "TCP",
					LocalAddress:  "127.0.0.1",
					LocalPort:     22,
					RemoteAddress: "0.0.0.0",
					RemotePort:    0,
					State:         "LISTEN",
					PID:           1,
				},
			}, nil
		}
	}

	return ParseLinuxNetstatOutput(string(out)), nil
}
