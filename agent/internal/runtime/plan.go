package runtime

import (
	"encoding/json"
	"fmt"
)

// ConditionClause represents a structured condition or logical combination in JOCKY.
// It can represent a leaf comparison (e.g. `field="signed", operator="eq", value=false`)
// or a composite logical operator (e.g. `operator="and", conditions=[...]`).
type ConditionClause struct {
	Field      string            `json:"field,omitempty"`
	Operator   string            `json:"operator"` // eq, neq, gt, lt, gte, lte, contains, in, and, or
	Value      any               `json:"value,omitempty"`
	Conditions []ConditionClause `json:"conditions,omitempty"`
}

// ExecutionStatement represents an individual operation inside a JOCKY execution plan.
type ExecutionStatement struct {
	Operation    string           `json:"operation"` // scan, collect, hash, check, flag, report
	Target       string           `json:"target,omitempty"`
	Targets      []string         `json:"targets,omitempty"`
	Path         string           `json:"path,omitempty"`
	CheckAgainst string           `json:"check_against,omitempty"`
	Against      string           `json:"against,omitempty"`
	Where        *ConditionClause `json:"where,omitempty"`
	Condition    *ConditionClause `json:"condition,omitempty"`
	Severity     string           `json:"severity,omitempty"`
	Destination  string           `json:"destination,omitempty"`
}

// ExecutionPlan represents the top-level deterministic JSON plan received from the management server.
type ExecutionPlan struct {
	Version    string               `json:"version"`
	Statements []ExecutionStatement `json:"statements"`
}

// ParseExecutionPlan parses raw JSON bytes into an ExecutionPlan struct.
func ParseExecutionPlan(data []byte) (*ExecutionPlan, error) {
	var plan ExecutionPlan
	if err := json.Unmarshal(data, &plan); err != nil {
		return nil, fmt.Errorf("failed to unmarshal JOCKY execution plan JSON: %w", err)
	}
	return &plan, nil
}
