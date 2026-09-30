package runtime

import (
	"strings"

	"github.com/jocky-dfir/jocky/agent/internal/collectors"
)

// HashRequest represents a request to hash files in a designated path.
type HashRequest struct {
	Target       string `json:"target"`
	Path         string `json:"path"`
	CheckAgainst string `json:"check_against,omitempty"`
}

// CheckRequest represents a standalone check instruction (e.g. against reputation).
type CheckRequest struct {
	Target string `json:"target"`
}

// FlagInstruction represents an alerting rule to be consumed by the detection engine.
type FlagInstruction struct {
	Condition ConditionClause `json:"condition"`
	Severity  string          `json:"severity,omitempty"`
}

// ReportInstruction represents a destination delivery instruction for telemetry results.
type ReportInstruction struct {
	Destination string `json:"destination"`
}

// ParsedPlan holds the structured domain requests and instructions decomposed from an ExecutionPlan.
type ParsedPlan struct {
	Version            string                        `json:"version"`
	CollectionRequests []collectors.CollectionRequest `json:"collection_requests"`
	HashRequests       []HashRequest                 `json:"hash_requests"`
	CheckRequests      []CheckRequest                `json:"check_requests"`
	FlagInstructions   []FlagInstruction             `json:"flag_instructions"`
	ReportInstructions []ReportInstruction           `json:"report_instructions"`
}

// TranslatePlan decomposes an ExecutionPlan into typed runtime requests and instructions.
func TranslatePlan(plan *ExecutionPlan, jobID string, agentID string) (*ParsedPlan, error) {
	if err := ValidatePlan(plan); err != nil {
		return nil, err
	}

	parsed := &ParsedPlan{
		Version:            plan.Version,
		CollectionRequests: make([]collectors.CollectionRequest, 0),
		HashRequests:       make([]HashRequest, 0),
		CheckRequests:      make([]CheckRequest, 0),
		FlagInstructions:   make([]FlagInstruction, 0),
		ReportInstructions: make([]ReportInstruction, 0),
	}

	for _, stmt := range plan.Statements {
		op := strings.ToLower(strings.TrimSpace(stmt.Operation))
		switch op {
		case "scan":
			target := strings.ToLower(strings.TrimSpace(stmt.Target))
			var conds []collectors.Condition
			if stmt.Where != nil {
				conds = append(conds, toCollectorCondition(*stmt.Where))
			}
			parsed.CollectionRequests = append(parsed.CollectionRequests, collectors.CollectionRequest{
				JobID:      jobID,
				AgentID:    agentID,
				Target:     target,
				Conditions: conds,
			})

		case "collect":
			targets := stmt.Targets
			if len(targets) == 0 && stmt.Target != "" {
				targets = []string{stmt.Target}
			}
			for _, t := range targets {
				tClean := strings.ToLower(strings.TrimSpace(t))
				req := collectors.CollectionRequest{
					JobID:   jobID,
					AgentID: agentID,
					Target:  tClean,
				}
				if stmt.Path != "" {
					req.Parameters = map[string]any{
						"path": stmt.Path,
					}
				}
				parsed.CollectionRequests = append(parsed.CollectionRequests, req)
			}

		case "hash":
			checkAgainst := stmt.CheckAgainst
			if checkAgainst == "" {
				checkAgainst = stmt.Against
			}
			target := stmt.Target
			if target == "" {
				target = "files"
			}
			parsed.HashRequests = append(parsed.HashRequests, HashRequest{
				Target:       target,
				Path:         stmt.Path,
				CheckAgainst: checkAgainst,
			})
			parsed.CollectionRequests = append(parsed.CollectionRequests, collectors.CollectionRequest{
				JobID:   jobID,
				AgentID: agentID,
				Target:  target,
				Parameters: map[string]any{
					"path":          stmt.Path,
					"hash":          true,
					"check_against": checkAgainst,
				},
			})

		case "check":
			against := stmt.Against
			if against == "" {
				against = stmt.CheckAgainst
			}
			parsed.CheckRequests = append(parsed.CheckRequests, CheckRequest{
				Target: against,
			})

		case "flag":
			var cond ConditionClause
			if stmt.Condition != nil {
				cond = *stmt.Condition
			}
			parsed.FlagInstructions = append(parsed.FlagInstructions, FlagInstruction{
				Condition: cond,
				Severity:  stmt.Severity,
			})

		case "report":
			parsed.ReportInstructions = append(parsed.ReportInstructions, ReportInstruction{
				Destination: stmt.Destination,
			})
		}
	}

	return parsed, nil
}

func toCollectorCondition(c ConditionClause) collectors.Condition {
	subConds := make([]collectors.Condition, 0, len(c.Conditions))
	for _, sub := range c.Conditions {
		subConds = append(subConds, toCollectorCondition(sub))
	}
	return collectors.Condition{
		Field:      c.Field,
		Operator:   c.Operator,
		Value:      c.Value,
		Conditions: subConds,
	}
}
