//go:build linux

package collectors

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"os/user"
	"path/filepath"
	"strconv"
	"strings"
)

func collectPlatformProcesses(ctx context.Context) ([]ProcessInfo, error) {
	entries, err := os.ReadDir("/proc")
	if err != nil {
		return nil, fmt.Errorf("failed to read /proc: %w", err)
	}

	var results []ProcessInfo

	for _, entry := range entries {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}

		if !entry.IsDir() {
			continue
		}

		pid, err := strconv.Atoi(entry.Name())
		if err != nil {
			// Not a process PID directory
			continue
		}

		procInfo := parseLinuxProcDir(pid)
		results = append(results, procInfo)
	}

	return results, nil
}

func parseLinuxProcDir(pid int) ProcessInfo {
	info := ProcessInfo{
		PID:             pid,
		SignatureStatus: "unsupported", // Linux ELF binaries do not have Authenticode signature semantics
	}

	procPath := fmt.Sprintf("/proc/%d", pid)

	// 1. Read Executable Path from /proc/[pid]/exe
	if exePath, err := os.Readlink(filepath.Join(procPath, "exe")); err == nil {
		info.Path = exePath
		info.Name = filepath.Base(exePath)
	}

	// 2. Read CommandLine from /proc/[pid]/cmdline
	if cmdData, err := os.ReadFile(filepath.Join(procPath, "cmdline")); err == nil && len(cmdData) > 0 {
		// Null-byte separated arguments
		parts := bytes.Split(cmdData, []byte{0})
		var cleanParts []string
		for _, p := range parts {
			if len(p) > 0 {
				cleanParts = append(cleanParts, string(p))
			}
		}
		info.CommandLine = strings.Join(cleanParts, " ")
		if info.Name == "" && len(cleanParts) > 0 {
			info.Name = filepath.Base(cleanParts[0])
		}
	}

	// 3. Read Status from /proc/[pid]/status
	if statusData, err := os.ReadFile(filepath.Join(procPath, "status")); err == nil {
		lines := strings.Split(string(statusData), "\n")
		for _, line := range lines {
			if strings.HasPrefix(line, "Name:") {
				nameVal := strings.TrimSpace(strings.TrimPrefix(line, "Name:"))
				if info.Name == "" {
					info.Name = nameVal
				}
			} else if strings.HasPrefix(line, "PPid:") {
				ppidStr := strings.TrimSpace(strings.TrimPrefix(line, "PPid:"))
				if ppid, err := strconv.Atoi(ppidStr); err == nil {
					info.ParentPID = ppid
				}
			} else if strings.HasPrefix(line, "Uid:") {
				uidFields := strings.Fields(strings.TrimPrefix(line, "Uid:"))
				if len(uidFields) > 0 {
					uidStr := uidFields[0]
					if u, err := user.LookupId(uidStr); err == nil {
						info.User = u.Username
					} else {
						info.User = uidStr
					}
				}
			}
		}
	}

	return info
}
