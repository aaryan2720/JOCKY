//go:build !windows && !linux

package collectors

import (
	"context"
)

func collectServices(ctx context.Context, options map[string]interface{}) ([]ServiceEntry, error) {
	_ = options
	return []ServiceEntry{}, nil
}
