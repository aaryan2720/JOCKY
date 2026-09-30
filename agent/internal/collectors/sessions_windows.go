//go:build windows

package collectors

import (
	"context"
	"os"
	"os/exec"
)

func collectSessions(ctx context.Context, options map[string]interface{}) ([]SessionEntry, error) {
	_ = options
	cmd := exec.CommandContext(ctx, "query", "session")
	out, err := cmd.Output()
	if err != nil {
		// Fallback to qwinsta or current user session
		cmd = exec.CommandContext(ctx, "qwinsta")
		out, err = cmd.Output()
		if err != nil {
			user := os.Getenv("USERNAME")
			if user == "" {
				user = "current_user"
			}
			return []SessionEntry{
				{
					Username:    user,
					SessionID:   "1",
					SessionName: "console",
					Terminal:    "console",
					State:       "Active",
					LogonType:   "Console",
					ClientName:  "",
					Source:      "local",
					LoginTime:   "",
				},
			}, nil
		}
	}

	return ParseQwinstaOutput(string(out)), nil
}
