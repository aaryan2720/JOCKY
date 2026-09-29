from typing import List, Optional
from app.jocky.lexer.tokens import Token
from app.jocky.ast.nodes import ScriptAST


class JockyParser:
    """
    Syntactical parser interface for JOCKY DSL.
    Builds an Abstract Syntax Tree (AST) from a sequence of tokens.
    """

    def __init__(self, tokens: Optional[List[Token]] = None):
        self.tokens = tokens or []
        self.cursor = 0

    def parse(self) -> ScriptAST:
        """
        Stub parser entry point.
        Full parser implementation deferred to language implementation phase.
        """
        # Placeholder returns an empty ScriptAST
        return ScriptAST(statements=[])
