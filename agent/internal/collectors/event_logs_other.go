//go:build !windows && !linux

package collectors

import (
	"context"
)

func collectEventLogs(ctx context.Context, options map[string]interface{}) ([]EventLogEntry, error) {
	_ = options
	return []EventLogEntry{}, nil
}
