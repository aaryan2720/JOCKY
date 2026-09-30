from typing import Dict, Any, List
import json
from app.jocky.ast.nodes import Program
from app.jocky.interpreter.interpreter import JockyInterpreter


class JockyPlanner:
    """
    Execution Planner for JOCKY DSL.
    Compiles typed AST into a deterministic, serializable JSON execution plan.
    """

    def __init__(self, ast: Program, version: str = "1"):
        self.ast = ast
        self.version = version
        self.interpreter = JockyInterpreter(ast)

    def build_execution_plan(self) -> Dict[str, Any]:
        """
        Builds the structured execution plan dictionary for the Go Agent / Runner.
        """
        statements = self.interpreter.evaluate_program()

        collectors = []
        checks = []
        for s in statements:
            if s.get("operation") == "collect":
                collectors.extend(s.get("targets", []))
            elif s.get("operation") == "scan":
                target = s.get("target")
                if target:
                    collectors.append(target)
            elif s.get("operation") == "check":
                checks.append(s)

        return {
            "version": self.version,
            "plan_version": f"{self.version}.0" if self.version == "1" else self.version,
            "statements": statements,
            "collectors": collectors,
            "checks": checks,
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Serializes the execution plan to a deterministic JSON formatted string.
        """
        plan = self.build_execution_plan()
        return json.dumps(plan, indent=indent, sort_keys=False)
