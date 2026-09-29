//go:build !windows && !linux

package collectors

import (
	"context"
	"fmt"
	"runtime"
)

func collectPlatformProcesses(ctx context.Context) ([]ProcessInfo, error) {
	return nil, fmt.Errorf("process collection is not supported on platform %s", runtime.GOOS)
}
