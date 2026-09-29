from typing import Optional, Any


class JockyError(Exception):
    """Base class for all JOCKY language exceptions."""
    pass


class JockyLexerError(JockyError):
    """Exception raised for errors during tokenization."""

    def __init__(self, message: str, line: int, column: int, character: Optional[str] = None):
        self.message = message
        self.line = line
        self.column = column
        self.character = character
        char_info = f" (unexpected character {character!r})" if character else ""
        super().__init__(f"Lexer Error at line {line}, column {column}: {message}{char_info}")


class JockyParserError(JockyError):
    """Exception raised for syntax/grammar errors during parsing."""

    def __init__(
        self,
        message: str,
        line: int,
        column: int,
        expected: Optional[str] = None,
        actual: Optional[Any] = None,
    ):
        self.message = message
        self.line = line
        self.column = column
        self.expected = expected
        self.actual = actual
        details = []
        if expected:
            details.append(f"expected: {expected}")
        if actual is not None:
            details.append(f"got: {actual}")
        detail_str = f" ({', '.join(details)})" if details else ""
        super().__init__(f"Parser Error at line {line}, column {column}: {message}{detail_str}")


class JockyValidationError(JockyError):
    """Exception raised for security policy violations or unsupported primitives."""

    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None):
        self.message = message
        self.line = line
        self.column = column
        loc = f" at line {line}, column {column}" if line is not None and column is not None else ""
        super().__init__(f"Validation Error{loc}: {message}")
