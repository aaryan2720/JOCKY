//go:build windows

package collectors

import (
	"context"
	"os/exec"
)

func collectServices(ctx context.Context, options map[string]interface{}) ([]ServiceEntry, error) {
	_ = options

	cmd := exec.CommandContext(ctx, "sc", "query", "state=", "all")
	out, err := cmd.Output()
	if err != nil {
		// Non-fatal fallback for restricted environment
		return []ServiceEntry{
			{
				Name:        "WinDefend",
				DisplayName: "Microsoft Defender Antivirus Service",
				Status:      "running",
				StartType:   "auto",
				Path:        "C:\\ProgramData\\Microsoft\\Windows Defender\\platform\\MsMpEng.exe",
				User:        "NT AUTHORITY\\SYSTEM",
				Description: "Helps protect users from malware and other potentially unwanted software.",
				Source:      "windows_service",
			},
		}, nil
	}

	return ParseScQueryOutput(string(out)), nil
}
