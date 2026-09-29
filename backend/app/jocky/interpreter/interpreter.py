from typing import Any, Dict
from app.jocky.ast.nodes import ScriptAST


class JockyInterpreter:
    """
    Interpreter interface for evaluating JOCKY scripts in-memory.
    Evaluates AST directly or validates logic without generating agent plans.
    """

    def __init__(self, ast: ScriptAST):
        self.ast = ast

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Placeholder evaluation method.
        Full interpreter logic deferred to language implementation phase.
        """
        return {"status": "unimplemented", "result": None}
