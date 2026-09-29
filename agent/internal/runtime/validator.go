package runtime

import (
	"fmt"
	"strings"
)

// PlanValidationError represents a structured error identified during plan validation.
type PlanValidationError struct {
	StatementIndex int    `json:"statement_index"`
	Field          string `json:"field"`
	Message        string `json:"message"`
}

func (e *PlanValidationError) Error() string {
	if e.StatementIndex >= 0 {
		return fmt.Sprintf("plan validation error at statement [%d] field '%s': %s", e.StatementIndex, e.Field, e.Message)
	}
	return fmt.Sprintf("plan validation error in field '%s': %s", e.Field, e.Message)
}

var supportedTargets = map[string]bool{
	"processes":       true,
	"connections":     true,
	"files":           true,
	"drivers":         true,
	"services":        true,
	"autoruns":        true,
	"scheduled_tasks": true,
	"users":           true,
	"sessions":        true,
	"event_logs":      true,
}

var supportedSeverities = map[string]bool{
	"low":      true,
	"medium":   true,
	"high":     true,
	"critical": true,
}

var supportedDestinations = map[string]bool{
	"console": true,
	"server":  true,
}

var supportedOperators = map[string]bool{
	"eq":            true,
	"neq":           true,
	"gt":            true,
	"lt":            true,
	"gte":           true,
	"lte":           true,
	"contains":      true,
	"in":            true,
	"injected_into": true,
	"and":           true,
	"or":            true,
	"==":            true,
	"!=":            true,
	">":             true,
	"<":             true,
	">=":            true,
	"<=":            true,
}

// ValidatePlan checks an ExecutionPlan for schema conformity, supported versions, targets, and operations.
func ValidatePlan(plan *ExecutionPlan) error {
	if plan == nil {
		return &PlanValidationError{
			StatementIndex: -1,
			Field:          "plan",
			Message:        "execution plan cannot be nil",
		}
	}

	if plan.Version != "1" {
		return &PlanValidationError{
			StatementIndex: -1,
			Field:          "version",
			Message:        fmt.Sprintf("unsupported plan version '%s', expected '1'", plan.Version),
		}
	}

	if len(plan.Statements) == 0 {
		return &PlanValidationError{
			StatementIndex: -1,
			Field:          "statements",
			Message:        "plan contains no statements",
		}
	}

	for i, stmt := range plan.Statements {
		if err := validateStatement(i, stmt); err != nil {
			return err
		}
	}

	return nil
}

func validateStatement(idx int, stmt ExecutionStatement) error {
	op := strings.ToLower(strings.TrimSpace(stmt.Operation))
	if op == "" {
		return &PlanValidationError{
			StatementIndex: idx,
			Field:          "operation",
			Message:        "operation cannot be empty",
		}
	}

	switch op {
	case "scan":
		target := strings.ToLower(strings.TrimSpace(stmt.Target))
		if target == "" {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          "target",
				Message:        "scan operation requires a non-empty target",
			}
		}
		if !supportedTargets[target] {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          "target",
				Message:        fmt.Sprintf("unsupported target '%s' for scan operation", stmt.Target),
			}
		}
		if stmt.Where != nil {
			if err := validateCondition(idx, "where", *stmt.Where); err != nil {
				return err
			}
		}

	case "collect":
		if len(stmt.Targets) == 0 {
			// Single target fallback if specified as Target
			if stmt.Target != "" {
				stmt.Targets = []string{stmt.Target}
			} else {
				return &PlanValidationError{
					StatementIndex: idx,
					Field:          "targets",
					Message:        "collect operation requires at least one target in 'targets'",
				}
			}
		}
		for _, t := range stmt.Targets {
			tClean := strings.ToLower(strings.TrimSpace(t))
			if !supportedTargets[tClean] {
				return &PlanValidationError{
					StatementIndex: idx,
					Field:          "targets",
					Message:        fmt.Sprintf("unsupported target '%s' in collect operation", t),
				}
			}
		}

	case "hash":
		if strings.TrimSpace(stmt.Path) == "" {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          "path",
				Message:        "hash operation requires a non-empty 'path'",
			}
		}
		if stmt.Target != "" && strings.ToLower(stmt.Target) != "files" {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          "target",
				Message:        fmt.Sprintf("hash operation only supports target 'files', got '%s'", stmt.Target),
			}
		}

	case "check":
		against := stmt.Against
		if against == "" {
			against = stmt.CheckAgainst
		}
		if strings.TrimSpace(against) == "" {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          "against",
				Message:        "check operation requires 'against' target (e.g. 'reputation')",
			}
		}

	case "flag":
		if stmt.Condition == nil {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          "condition",
				Message:        "flag operation requires a 'condition'",
			}
		}
		if err := validateCondition(idx, "condition", *stmt.Condition); err != nil {
			return err
		}
		if stmt.Severity != "" {
			sevClean := strings.ToLower(strings.TrimSpace(stmt.Severity))
			if !supportedSeverities[sevClean] {
				return &PlanValidationError{
					StatementIndex: idx,
					Field:          "severity",
					Message:        fmt.Sprintf("invalid severity '%s', expected low, medium, high, or critical", stmt.Severity),
				}
			}
		}

	case "report":
		dest := strings.ToLower(strings.TrimSpace(stmt.Destination))
		if dest == "" {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          "destination",
				Message:        "report operation requires a 'destination'",
			}
		}
		if !supportedDestinations[dest] {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          "destination",
				Message:        fmt.Sprintf("invalid report destination '%s', expected console or server", stmt.Destination),
			}
		}

	default:
		return &PlanValidationError{
			StatementIndex: idx,
			Field:          "operation",
			Message:        fmt.Sprintf("unsupported operation '%s'", stmt.Operation),
		}
	}

	return nil
}

func validateCondition(idx int, fieldName string, cond ConditionClause) error {
	op := strings.ToLower(strings.TrimSpace(cond.Operator))
	if op == "" {
		return &PlanValidationError{
			StatementIndex: idx,
			Field:          fieldName + ".operator",
			Message:        "condition operator cannot be empty",
		}
	}

	if !supportedOperators[op] {
		return &PlanValidationError{
			StatementIndex: idx,
			Field:          fieldName + ".operator",
			Message:        fmt.Sprintf("unsupported condition operator '%s'", cond.Operator),
		}
	}

	if op == "and" || op == "or" {
		if len(cond.Conditions) == 0 {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          fieldName + ".conditions",
				Message:        fmt.Sprintf("logical '%s' operator requires non-empty sub-conditions", op),
			}
		}
		for subIdx, subCond := range cond.Conditions {
			subField := fmt.Sprintf("%s.conditions[%d]", fieldName, subIdx)
			if err := validateCondition(idx, subField, subCond); err != nil {
				return err
			}
		}
	} else {
		if strings.TrimSpace(cond.Field) == "" {
			return &PlanValidationError{
				StatementIndex: idx,
				Field:          fieldName + ".field",
				Message:        "comparison condition requires a non-empty field name",
			}
		}
	}

	return nil
}
