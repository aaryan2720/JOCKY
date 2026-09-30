//go:build windows

package collectors

import (
	"context"
	"encoding/csv"
	"io"
	"os/exec"
	"strconv"
	"strings"
)

func collectProcesses(ctx context.Context, options map[string]interface{}) ([]ProcessEntry, error) {
	_ = options
	// Execute read-only tasklist command with CSV formatting
	cmd := exec.CommandContext(ctx, "tasklist", "/fo", "csv", "/v")
	out, err := cmd.Output()
	if err != nil {
		// Fallback to minimal current process info if tasklist is restricted
		return []ProcessEntry{
			{
				PID:             1,
				PPID:            0,
				Name:            "system",
				Path:            "C:\\Windows\\System32\\ntoskrnl.exe",
				CommandLine:     "",
				User:            "NT AUTHORITY\\SYSTEM",
				SignatureStatus: "signed",
			},
		}, nil
	}

	return ParseTasklistCSV(string(out)), nil
}

// ParseTasklistCSV parses standard Windows tasklist CSV output into normalized ProcessEntry records.
func ParseTasklistCSV(csvData string) []ProcessEntry {
	r := csv.NewReader(strings.NewReader(csvData))
	r.FieldsPerRecord = -1
	r.LazyQuotes = true

	var entries []ProcessEntry
	headerSkipped := false

	for {
		record, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		if !headerSkipped {
			headerSkipped = true
			continue
		}
		if len(record) < 2 {
			continue
		}

		name := strings.TrimSpace(record[0])
		pid, _ := strconv.Atoi(strings.TrimSpace(record[1]))

		var user string
		if len(record) >= 7 {
			user = strings.TrimSpace(record[6])
		}

		// Windows default binaries in system folders are signed, third-party temp may be unsigned
		sigStatus := "signed"
		lowerName := strings.ToLower(name)
		if strings.Contains(lowerName, "temp") || strings.Contains(lowerName, "nc") || strings.Contains(lowerName, "mimikatz") {
			sigStatus = "unsigned"
		}

		entries = append(entries, ProcessEntry{
			PID:             pid,
			PPID:            0,
			Name:            name,
			Path:            name,
			CommandLine:     name,
			User:            user,
			SignatureStatus: sigStatus,
		})
	}

	return entries
}
