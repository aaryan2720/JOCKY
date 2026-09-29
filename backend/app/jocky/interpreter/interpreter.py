from typing import Any, Dict, List, Union
from app.jocky.ast.nodes import (
    Program,
    Statement,
    ScanStatement,
    CollectStatement,
    HashStatement,
    CheckStatement,
    FlagStatement,
    ReportStatement,
    Condition,
    Comparison,
    BinaryCondition,
)

OPERATOR_CANONICAL_MAP = {
    "==": "eq",
    "!=": "neq",
    ">": "gt",
    "<": "lt",
    ">=": "gte",
    "<=": "lte",
    "contains": "contains",
    "in": "in",
}


def canonicalize_operator(op: str) -> str:
    op_lower = op.lower()
    return OPERATOR_CANONICAL_MAP.get(op_lower, op_lower)


class JockyInterpreter:
    """
    AST Visitor and Intermediate Representation (IR) lowerer.
    Transforms typed AST nodes into structured intermediate dictionary representations.
    Strictly read-only; never interacts with system primitives or host execution.
    """

    def __init__(self, ast: Program):
        self.ast = ast

    def evaluate_program(self) -> List[Dict[str, Any]]:
        """Transforms all AST statements in the program into intermediate representation dictionaries."""
        return [self.evaluate_statement(stmt) for stmt in self.ast.statements]

    def evaluate_statement(self, stmt: Statement) -> Dict[str, Any]:
        if isinstance(stmt, ScanStatement):
            res: Dict[str, Any] = {
                "operation": "scan",
                "target": stmt.target,
            }
            if stmt.condition:
                res["where"] = self.evaluate_condition(stmt.condition)
            return res

        elif isinstance(stmt, CollectStatement):
            return {
                "operation": "collect",
                "targets": list(stmt.targets),
            }

        elif isinstance(stmt, HashStatement):
            res = {
                "operation": "hash",
                "target": "files",
                "path": stmt.path,
            }
            if stmt.check_against:
                res["check_against"] = stmt.check_against
            return res

        elif isinstance(stmt, CheckStatement):
            return {
                "operation": "check",
                "against": stmt.target,
            }

        elif isinstance(stmt, FlagStatement):
            res = {
                "operation": "flag",
                "condition": self.evaluate_condition(stmt.condition),
            }
            if stmt.severity:
                res["severity"] = stmt.severity
            return res

        elif isinstance(stmt, ReportStatement):
            return {
                "operation": "report",
                "destination": stmt.destination,
            }

        else:
            raise TypeError(f"Unknown statement type: {type(stmt).__name__}")

    def evaluate_condition(self, cond: Condition) -> Dict[str, Any]:
        if isinstance(cond, Comparison):
            return {
                "field": cond.field,
                "operator": canonicalize_operator(cond.operator),
                "value": cond.value,
            }
        elif isinstance(cond, BinaryCondition):
            # Flatten homogeneous binary chains (e.g. (A and B) and C -> [A, B, C])
            conditions = self._flatten_binary_condition(cond, cond.operator)
            return {
                "operator": cond.operator.lower(),
                "conditions": conditions,
            }
        else:
            raise TypeError(f"Unknown condition node: {type(cond).__name__}")

    def _flatten_binary_condition(self, cond: Condition, target_operator: str) -> List[Dict[str, Any]]:
        if isinstance(cond, BinaryCondition) and cond.operator.lower() == target_operator.lower():
            left_items = self._flatten_binary_condition(cond.left, target_operator)
            right_items = self._flatten_binary_condition(cond.right, target_operator)
            return left_items + right_items
        else:
            return [self.evaluate_condition(cond)]
