//go:build linux

package collectors

import (
	"context"
	"os"
	"os/exec"
)

func collectDrivers(ctx context.Context, options map[string]interface{}) ([]DriverEntry, error) {
	_ = options

	// 1. Direct /proc/modules read
	if data, err := os.ReadFile("/proc/modules"); err == nil && len(data) > 0 {
		return ParseProcModules(string(data)), nil
	}

	// 2. Fallback to lsmod
	cmd := exec.CommandContext(ctx, "lsmod")
	if out, err := cmd.Output(); err == nil && len(out) > 0 {
		return ParseProcModules(string(out)), nil
	}

	return []DriverEntry{}, nil
}
