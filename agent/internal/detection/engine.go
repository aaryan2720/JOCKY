package detection

import (
	"context"

	"github.com/jocky-dfir/jocky/agent/internal/collectors"
)

// MatchResult represents an alert produced by local agent rule matching.
type MatchResult struct {
	RuleName    string                 `json:"rule_name"`
	Severity    string                 `json:"severity"`
	Evidence    map[string]interface{} `json:"evidence"`
	Explanation string                 `json:"explanation"`
}

// LocalEngine defines the contract for running in-memory YARA/heuristic detection on agent.
type LocalEngine interface {
	ScanArtifacts(ctx context.Context, artifacts []collectors.Artifact) ([]MatchResult, error)
}
