package collectors

import (
	"context"
	"strings"
	"time"
)

// SessionEntry represents a normalized logged-in user session.
type SessionEntry struct {
	Username    string `json:"username"`
	SessionID   string `json:"session_id"`
	SessionName string `json:"session_name"`
	Terminal    string `json:"terminal"`
	State       string `json:"state"`
	LogonType   string `json:"logon_type"`
	ClientName  string `json:"client_name"`
	Source      string `json:"source"`
	LoginTime   string `json:"login_time"`
}

// SessionCollector collects active logged-in endpoint sessions.
type SessionCollector struct{}

// NewSessionCollector creates a new SessionCollector instance.
func NewSessionCollector() *SessionCollector {
	return &SessionCollector{}
}

func (c *SessionCollector) Name() string {
	return "sessions"
}

func (c *SessionCollector) Supports(target string) bool {
	return target == "sessions"
}

// Collect enumerates active logon sessions in read-only mode without inspecting credentials.
func (c *SessionCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	entries, err := collectSessions(ctx, request.Parameters)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, s := range entries {
		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        "session",
			CollectedAt: now,
			Data: map[string]interface{}{
				"username":     s.Username,
				"session_id":   s.SessionID,
				"session_name": s.SessionName,
				"terminal":     s.Terminal,
				"state":        s.State,
				"logon_type":   s.LogonType,
				"client_name":  s.ClientName,
				"source":       s.Source,
				"login_time":   s.LoginTime,
			},
		})
	}

	return artifacts, nil
}

// ParseQwinstaOutput parses Windows qwinsta command output into SessionEntry.
func ParseQwinstaOutput(output string) []SessionEntry {
	lines := strings.Split(output, "\n")
	var entries []SessionEntry

	for i, line := range lines {
		if i == 0 || strings.TrimSpace(line) == "" {
			continue // skip header or blank
		}

		fields := strings.Fields(line)
		if len(fields) < 2 {
			continue
		}

		sessName := strings.TrimPrefix(fields[0], ">")
		username := ""
		sessID := ""
		state := ""

		if len(fields) >= 4 && (fields[2] == "Active" || fields[2] == "Disc" || fields[2] == "Conn") {
			// e.g. services 0 Disc
			sessID = fields[1]
			state = fields[2]
		} else if len(fields) >= 4 {
			// e.g. >console Alice 1 Active
			username = fields[1]
			sessID = fields[2]
			state = fields[3]
		} else if len(fields) >= 3 {
			sessID = fields[1]
			state = fields[2]
		}

		logonType := "Console"
		if strings.HasPrefix(strings.ToLower(sessName), "rdp") {
			logonType = "RDP"
		} else if strings.EqualFold(sessName, "services") {
			logonType = "Service"
		}

		entries = append(entries, SessionEntry{
			Username:    username,
			SessionID:   sessID,
			SessionName: sessName,
			State:       state,
			LogonType:   logonType,
		})
	}

	return entries
}

// ParseWhoOutput parses Unix `who` output into SessionEntry.
func ParseWhoOutput(output string) []SessionEntry {
	lines := strings.Split(output, "\n")
	var entries []SessionEntry

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		fields := strings.Fields(line)
		if len(fields) < 2 {
			continue
		}

		user := fields[0]
		term := fields[1]
		source := ""
		loginTime := ""

		if len(fields) >= 4 {
			loginTime = fields[2] + " " + fields[3]
		}
		if len(fields) >= 5 {
			source = strings.Trim(fields[4], "()")
		}

		logonType := "Console"
		if strings.HasPrefix(term, "pts") {
			logonType = "PTS"
		} else if strings.HasPrefix(term, "tty") {
			logonType = "Console"
		}

		entries = append(entries, SessionEntry{
			Username:  user,
			Terminal:  term,
			Source:    source,
			LoginTime: loginTime,
			LogonType: logonType,
			State:     "Active",
		})
	}

	return entries
}
