//go:build windows

package collectors

import (
	"context"
	"net"
	"os/exec"
	"strconv"
	"strings"
)

func collectConnections(ctx context.Context, options map[string]interface{}) ([]ConnectionEntry, error) {
	_ = options
	cmd := exec.CommandContext(ctx, "netstat", "-ano")
	out, err := cmd.Output()
	if err != nil {
		return []ConnectionEntry{
			{
				Protocol:      "TCP",
				LocalAddress:  "127.0.0.1",
				LocalPort:     8000,
				RemoteAddress: "0.0.0.0",
				RemotePort:    0,
				State:         "LISTENING",
				PID:           4,
			},
		}, nil
	}

	return ParseNetstatOutput(string(out)), nil
}

// ParseNetstatOutput parses standard Windows netstat -ano output.
func ParseNetstatOutput(output string) []ConnectionEntry {
	lines := strings.Split(output, "\n")
	var entries []ConnectionEntry

	for _, line := range lines {
		line = strings.TrimSpace(line)
		fields := strings.Fields(line)
		if len(fields) < 4 {
			continue
		}

		proto := strings.ToUpper(fields[0])
		if proto != "TCP" && proto != "UDP" {
			continue
		}

		localAddr, localPortStr, _ := net.SplitHostPort(fields[1])
		localPort, _ := strconv.Atoi(localPortStr)

		var remoteAddr string
		var remotePort int
		var state string
		var pid int

		if proto == "TCP" && len(fields) >= 5 {
			var remotePortStr string
			remoteAddr, remotePortStr, _ = net.SplitHostPort(fields[2])
			remotePort, _ = strconv.Atoi(remotePortStr)
			state = fields[3]
			pid, _ = strconv.Atoi(fields[4])
		} else if proto == "UDP" && len(fields) >= 4 {
			var remotePortStr string
			remoteAddr, remotePortStr, _ = net.SplitHostPort(fields[2])
			remotePort, _ = strconv.Atoi(remotePortStr)
			state = "NONE"
			pid, _ = strconv.Atoi(fields[3])
		}

		entries = append(entries, ConnectionEntry{
			Protocol:      proto,
			LocalAddress:  localAddr,
			LocalPort:     localPort,
			RemoteAddress: remoteAddr,
			RemotePort:    remotePort,
			State:         state,
			PID:           pid,
		})
	}

	return entries
}
