//go:build !windows && !linux

package collectors

import (
	"context"
	"fmt"
	"runtime"
)

func collectPlatformConnections(ctx context.Context) ([]NetworkConnectionInfo, error) {
	return nil, fmt.Errorf("network collection is not supported on platform %s", runtime.GOOS)
}
