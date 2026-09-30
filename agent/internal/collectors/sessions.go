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

// Collect enumerates active logon sessions in read-only mode without inspecting credentials.
func (c *SessionCollector) Collect(ctx context.Context, options map[string]interface{}) ([]Artifact, error) {
	entries, err := collectSessions(ctx, options)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, s := range entries {
		artifacts = append(artifacts, Artifact{
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

// ParseQwinstaOutput parses Windows `query session` or `qwinsta` output into SessionEntry records.
// Typical output format:
//
//	SESSIONNAME       USERNAME                 ID  STATE    TYPE        DEVICE
//	services                                    0  Disc
//	>console           Alice                     1  Active
//	rdp-tcp#1         Bob                       2  Active
func ParseQwinstaOutput(output string) []SessionEntry {
	lines := strings.Split(output, "\n")
	var entries []SessionEntry

	for i, line := range lines {
		line = strings.TrimSpace(line)
		if i == 0 || line == "" {
			continue // skip header or empty
		}

		// Clean up leading active indicator '>'
		cleanLine := strings.TrimPrefix(line, ">")
		cleanLine = strings.TrimSpace(cleanLine)
		fields := strings.Fields(cleanLine)
		if len(fields) < 3 {
			continue
		}

		var sessionName, username, sessionID, state, logonType string

		// If field count is 3: sessionName (or empty), sessionID, state
		// If field count >= 4: sessionName, username, id, state
		if len(fields) == 3 {
			sessionName = fields[0]
			username = "SYSTEM"
			sessionID = fields[1]
			state = fields[2]
		} else {
			sessionName = fields[0]
			username = fields[1]
			sessionID = fields[2]
			state = fields[3]
		}

		logonType = "Interactive"
		if strings.Contains(strings.ToLower(sessionName), "rdp") {
			logonType = "RDP"
		} else if strings.EqualFold(sessionName, "console") {
			logonType = "Console"
		} else if strings.EqualFold(sessionName, "services") {
			logonType = "Service"
		}

		entries = append(entries, SessionEntry{
			Username:    username,
			SessionID:   sessionID,
			SessionName: sessionName,
			Terminal:    sessionName,
			State:       state,
			LogonType:   logonType,
			ClientName:  "",
			Source:      "local",
			LoginTime:   "",
		})
	}

	return entries
}

// ParseWhoOutput parses standard UNIX `who` output into SessionEntry records.
// Typical format:
//
//	alice    tty1         2026-09-30 08:30 (:0)
//	bob      pts/0        2026-09-30 09:15 (192.168.1.50)
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

		username := fields[0]
		terminal := fields[1]
		loginTime := ""
		source := "local"

		if len(fields) >= 4 {
			loginTime = fields[2] + " " + fields[3]
		}
		if len(fields) >= 5 {
			source = strings.Trim(fields[4], "()")
		}

		logonType := "Console"
		if strings.HasPrefix(terminal, "pts") {
			logonType = "PTS"
		}

		entries = append(entries, SessionEntry{
			Username:    username,
			SessionID:   terminal,
			SessionName: terminal,
			Terminal:    terminal,
			State:       "Active",
			LogonType:   logonType,
			ClientName:  source,
			Source:      source,
			LoginTime:   loginTime,
		})
	}

	return entries
}
