from typing import Dict, Any
from app.jocky.ast.nodes import ScriptAST


class JockyPlanner:
    """
    Execution Planner interface for JOCKY DSL.
    Compiles an AST into a deterministic, serializable JSON execution plan
    dispatched to Go fleet agents.
    """

    def __init__(self, ast: ScriptAST):
        self.ast = ast

    def build_execution_plan(self) -> Dict[str, Any]:
        """
        Placeholder execution planner method.
        Builds the JSON execution plan for Go agents.
        """
        return {
            "plan_version": "1.0",
            "collectors": [],
            "checks": [],
        }
