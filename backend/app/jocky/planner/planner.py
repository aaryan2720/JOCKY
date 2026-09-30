from typing import Dict, Any
from app.jocky.ast.nodes import ScriptAST, CollectStatement, CheckStatement


class JockyPlanner:
    """
    Execution Planner interface for JOCKY DSL.
    Compiles an AST into a deterministic, serializable JSON execution plan
    dispatched to Go fleet agents.
    """

    def __init__(self, ast: ScriptAST):
        self.ast = ast

    def build_execution_plan(self) -> Dict[str, Any]:
        """Build the JSON execution plan for Go agents from AST."""
        collectors = []
        checks = []
        if self.ast and hasattr(self.ast, "statements"):
            for stmt in self.ast.statements:
                if isinstance(stmt, CollectStatement):
                    collector_entry = {"target": stmt.collector_type}
                    if stmt.filters:
                        collector_entry["filters"] = stmt.filters
                    if stmt.options:
                        collector_entry["options"] = stmt.options
                    collectors.append(collector_entry)
                elif isinstance(stmt, CheckStatement):
                    checks.append({
                        "engine": stmt.engine,
                        "rule": stmt.rule_identifier,
                        "field": stmt.target_field,
                    })

        return {
            "plan_version": "1.0",
            "collectors": collectors,
            "checks": checks,
        }

