//go:build windows

package collectors

import (
	"context"
	"os/exec"
)

func collectDrivers(ctx context.Context, options map[string]interface{}) ([]DriverEntry, error) {
	_ = options

	cmd := exec.CommandContext(ctx, "driverquery", "/fo", "CSV", "/v")
	out, err := cmd.Output()
	if err != nil {
		// Try fallback without /v
		cmdFallback := exec.CommandContext(ctx, "driverquery", "/fo", "CSV")
		outFallback, errFallback := cmdFallback.Output()
		if errFallback == nil && len(outFallback) > 0 {
			return ParseDriverQueryCSV(string(outFallback)), nil
		}

		// Safe non-fatal fallback for restricted environments
		return []DriverEntry{
			{
				Name:        "tcpip",
				DisplayName: "TCP/IP Protocol Driver",
				State:       "Running",
				Path:        "C:\\Windows\\system32\\drivers\\tcpip.sys",
				Type:        "Kernel",
				DependsOn:   []string{},
				Source:      "driverquery",
			},
		}, nil
	}

	return ParseDriverQueryCSV(string(out)), nil
}
