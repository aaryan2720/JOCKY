//go:build !windows && !linux

package collectors

import (
	"context"
)

func collectDrivers(ctx context.Context, options map[string]interface{}) ([]DriverEntry, error) {
	_ = options
	return []DriverEntry{}, nil
}
