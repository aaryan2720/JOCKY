from typing import List, Optional
from app.jocky.lexer.tokens import Token, TokenType
from app.jocky.ast.nodes import ScriptAST, CollectStatement, CheckStatement, AlertStatement, TargetStatement


class JockyParser:
    """
    Syntactical parser interface for JOCKY DSL.
    Builds an Abstract Syntax Tree (AST) from a sequence of tokens.
    """

    def __init__(self, tokens: Optional[List[Token]] = None):
        self.tokens = tokens or []
        self.cursor = 0

    def parse(self) -> ScriptAST:
        """Parse token sequence into ScriptAST statements."""
        statements = []
        i = 0
        VALID_STATEMENT_VERBS = {
            "COLLECT", "SCAN", "CHECK", "ALERT", "FLAG", "TARGET", "REPORT", "HASH"
        }

        while i < len(self.tokens):
            tok = self.tokens[i]
            if tok.type in (TokenType.SEMICOLON, TokenType.EOF):
                i += 1
                continue

            val_upper = str(tok.value).upper()
            if val_upper not in VALID_STATEMENT_VERBS and tok.type not in (
                TokenType.COLLECT, TokenType.TARGET, TokenType.CHECK, TokenType.ALERT
            ):
                raise ValueError(
                    f"Syntax error at line {tok.line}, col {tok.column}: "
                    f"Unrecognized JOCKY statement verb '{tok.value}'"
                )

            if tok.type == TokenType.COLLECT or val_upper in ("COLLECT", "SCAN"):
                if i + 1 < len(self.tokens):
                    target_tok = self.tokens[i + 1]
                    if target_tok.type not in (TokenType.SEMICOLON, TokenType.EOF):
                        collector_type = str(target_tok.value).lower()
                        statements.append(CollectStatement(collector_type=collector_type))
                        i += 2
                        # Skip until semicolon or EOF
                        while i < len(self.tokens) and self.tokens[i].type != TokenType.SEMICOLON:
                            i += 1
                        continue
            i += 1
        return ScriptAST(statements=statements)


