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

func (c *UserCollector) Supports(target string) bool {
	return target == "users"
}

// Collect queries local accounts without accessing credentials or password hashes.
func (c *UserCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	entries, err := collectUsers(ctx, request.Parameters)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, u := range entries {
		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
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

// ParsePasswd parses Unix /etc/passwd file content into UserEntry records.
func ParsePasswd(content string) []UserEntry {
	lines := strings.Split(content, "\n")
	var entries []UserEntry

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		fields := strings.Split(line, ":")
		if len(fields) < 7 {
			continue
		}

		username := fields[0]
		uid, _ := strconv.Atoi(fields[2])
		gid, _ := strconv.Atoi(fields[3])
		desc := fields[4]
		home := fields[5]
		shell := fields[6]

		enabled := true
		if strings.Contains(shell, "nologin") || strings.Contains(shell, "false") {
			enabled = false
		}

		accountType := "service"
		if uid == 0 {
			accountType = "root"
		} else if uid >= 1000 && uid < 65534 {
			accountType = "local"
		}

		entries = append(entries, UserEntry{
			Username:    username,
			UID:         uid,
			GID:         gid,
			Description: desc,
			HomeDir:     home,
			Shell:       shell,
			Enabled:     enabled,
			AccountType: accountType,
		})
	}

	return entries
}

// ParseNetUserList parses Windows `net user` command output to extract local usernames.
func ParseNetUserList(output string) []UserEntry {
	lines := strings.Split(output, "\n")
	var entries []UserEntry
	separatorFound := false

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "----") {
			separatorFound = true
			continue
		}
		if !separatorFound {
			continue
		}
		if strings.Contains(line, "command completed successfully") || line == "" {
			continue
		}

		fields := strings.Fields(line)
		for _, name := range fields {
			accountType := "local"
			if strings.EqualFold(name, "Administrator") {
				accountType = "admin"
			} else if strings.EqualFold(name, "Guest") || strings.EqualFold(name, "DefaultAccount") {
				accountType = "system"
			}

			entries = append(entries, UserEntry{
				Username:    name,
				AccountType: accountType,
				Enabled:     true,
			})
		}
	}

	return entries
}
