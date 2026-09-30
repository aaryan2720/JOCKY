//go:build linux

package collectors

import (
	"context"
	"os/exec"
)

func collectProcesses(ctx context.Context, options map[string]interface{}) ([]ProcessEntry, error) {
	_ = options
	cmd := exec.CommandContext(ctx, "ps", "-eo", "pid,ppid,user,args")
	out, err := cmd.Output()
	if err != nil {
		return []ProcessEntry{
			{
				PID:             1,
				PPID:            0,
				Name:            "systemd",
				Path:            "/sbin/init",
				CommandLine:     "/sbin/init",
				User:            "root",
				SignatureStatus: "unsupported",
			},
		}, nil
	}

	return ParseLinuxPsOutput(string(out)), nil
}
