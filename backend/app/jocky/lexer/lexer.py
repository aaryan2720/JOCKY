from typing import List
from app.jocky.lexer.tokens import Token, TokenType


class JockyLexer:
    """
    Lexical analyzer interface for JOCKY DSL.
    Tokenizes raw JOCKY source script into a stream of Tokens.
    """

    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        """
        Stub tokenization entry point.
        Full lexer implementation deferred to implementation phase.
        """
        # Placeholder returns EOF token
        return [Token(type=TokenType.EOF, value=None, line=self.line, column=self.column)]
