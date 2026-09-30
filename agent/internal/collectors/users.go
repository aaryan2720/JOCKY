package collectors

import (
	"context"
	"strconv"
	"strings"
	"time"
)

// UserEntry represents a normalized local user account record.
type UserEntry struct {
	Username    string `json:"username"`
	SID         string `json:"sid"`
	UID         int    `json:"uid"`
	GID         int    `json:"gid"`
	HomeDir     string `json:"home_dir"`
	Shell       string `json:"shell"`
	Enabled     bool   `json:"enabled"`
	AccountType string `json:"account_type"`
	Description string `json:"description"`
}

// UserCollector collects read-only information on local user accounts.
type UserCollector struct{}

// NewUserCollector creates an instance of UserCollector.
func NewUserCollector() *UserCollector {
	return &UserCollector{}
}

func (c *UserCollector) Name() string {
	return "users"
}

// Collect queries local accounts without accessing credentials or password hashes.
func (c *UserCollector) Collect(ctx context.Context, options map[string]interface{}) ([]Artifact, error) {
	entries, err := collectUsers(ctx, options)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, u := range entries {
		artifacts = append(artifacts, Artifact{
			Type:        "user",
			CollectedAt: now,
			Data: map[string]interface{}{
				"username":     u.Username,
				"sid":          u.SID,
				"uid":          u.UID,
				"gid":          u.GID,
				"home_dir":     u.HomeDir,
				"shell":        u.Shell,
				"enabled":      u.Enabled,
				"account_type": u.AccountType,
				"description":  u.Description,
			},
		})
	}

	return artifacts, nil
}

// ParsePasswd parses standard UNIX /etc/passwd file contents into normalized UserEntry records.
// Line format: username:password:uid:gid:gecos:home_dir:shell
func ParsePasswd(content string) []UserEntry {
	lines := strings.Split(content, "\n")
	var entries []UserEntry

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.Split(line, ":")
		if len(parts) < 7 {
			continue
		}

		username := parts[0]
		uid, _ := strconv.Atoi(parts[2])
		gid, _ := strconv.Atoi(parts[3])
		description := parts[4]
		homeDir := parts[5]
		shell := parts[6]

		// Determine enabled status based on valid interactive shell
		enabled := true
		lowerShell := strings.ToLower(shell)
		if strings.Contains(lowerShell, "nologin") || strings.Contains(lowerShell, "false") {
			enabled = false
		}

		accountType := "system"
		if uid >= 1000 && uid < 65534 {
			accountType = "local"
		} else if uid == 0 {
			accountType = "root"
		}

		entries = append(entries, UserEntry{
			Username:    username,
			SID:         "",
			UID:         uid,
			GID:         gid,
			HomeDir:     homeDir,
			Shell:       shell,
			Enabled:     enabled,
			AccountType: accountType,
			Description: description,
		})
	}

	return entries
}

// ParseNetUserList parses Windows `net user` summary list output.
func ParseNetUserList(output string) []UserEntry {
	lines := strings.Split(output, "\n")
	var entries []UserEntry
	separatorPassed := false

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "---") {
			separatorPassed = true
			continue
		}
		if !separatorPassed || strings.HasPrefix(line, "The command completed") {
			continue
		}

		// Users are listed in columns
		names := strings.Fields(line)
		for _, name := range names {
			name = strings.TrimSpace(name)
			if name == "" {
				continue
			}

			accountType := "local"
			enabled := true
			lower := strings.ToLower(name)
			if lower == "administrator" || lower == "guest" || strings.HasPrefix(lower, "default") {
				accountType = "system"
			}
			if lower == "guest" {
				enabled = false
			}

			entries = append(entries, UserEntry{
				Username:    name,
				SID:         "",
				UID:         0,
				GID:         0,
				HomeDir:     "C:\\Users\\" + name,
				Shell:       "cmd.exe",
				Enabled:     enabled,
				AccountType: accountType,
				Description: "",
			})
		}
	}

	return entries
}
