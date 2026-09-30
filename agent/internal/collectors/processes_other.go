//go:build !windows && !linux

package collectors

import (
	"context"
	"os"
)

func collectProcesses(ctx context.Context, options map[string]interface{}) ([]ProcessEntry, error) {
	_ = ctx
	_ = options
	return []ProcessEntry{
		{
			PID:             os.Getpid(),
			PPID:            os.Getppid(),
			Name:            "jocky-agent",
			Path:            "/agent",
			CommandLine:     "jocky-agent",
			User:            "agent",
			SignatureStatus: "unsupported",
		},
	}, nil
}
