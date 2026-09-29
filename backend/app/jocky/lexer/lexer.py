from typing import List, Optional
from app.jocky.lexer.tokens import Token, TokenType, KEYWORDS
from app.jocky.errors import JockyLexerError


class JockyLexer:
    """
    Lexical analyzer for JOCKY DSL.
    Tokenizes raw JOCKY source script into a stream of Token instances.
    """

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.position = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> Optional[str]:
        pos = self.position + offset
        if pos < self.length:
            return self.source[pos]
        return None

    def _advance(self) -> str:
        char = self.source[self.position]
        self.position += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.position < self.length:
            char = self._peek()

            # 1. Skip Whitespace
            if char in (" ", "\t", "\r", "\n"):
                self._advance()
                continue

            # 2. Skip Comments starting with '#'
            if char == "#":
                while self.position < self.length and self._peek() != "\n":
                    self._advance()
                continue

            start_line = self.line
            start_col = self.column

            # 3. String Literals ("..." or '...')
            if char in ('"', "'"):
                quote_type = self._advance()
                value_chars = []
                closed = False

                while self.position < self.length:
                    curr = self._peek()
                    if curr == "\\":
                        self._advance()
                        next_char = self._peek()
                        if next_char is None:
                            raise JockyLexerError("Unfinished escape sequence in string", self.line, self.column)
                        escape_map = {
                            "n": "\n",
                            "t": "\t",
                            "r": "\r",
                            "\\": "\\",
                            '"': '"',
                            "'": "'",
                        }
                        value_chars.append(escape_map.get(next_char, next_char))
                        self._advance()
                    elif curr == quote_type:
                        self._advance()
                        closed = True
                        break
                    elif curr == "\n":
                        raise JockyLexerError("Unclosed string literal across newlines", start_line, start_col)
                    else:
                        value_chars.append(self._advance())

                if not closed:
                    raise JockyLexerError(f"Unclosed string literal starting with {quote_type}", start_line, start_col)

                tokens.append(Token(TokenType.STRING, "".join(value_chars), start_line, start_col))
                continue

            # 4. Numbers (Integer / Float)
            if char.isdigit():
                num_chars = []
                has_dot = False
                while self.position < self.length:
                    c = self._peek()
                    if c is not None and c.isdigit():
                        num_chars.append(self._advance())
                    elif c == "." and not has_dot and (self._peek(1) is not None and self._peek(1).isdigit()):
                        has_dot = True
                        num_chars.append(self._advance())
                    else:
                        break

                raw_num = "".join(num_chars)
                num_val = float(raw_num) if has_dot else int(raw_num)
                tokens.append(Token(TokenType.NUMBER, num_val, start_line, start_col))
                continue

            # 5. Multi-character and Single-character Operators & Punctuation
            if char == "=":
                self._advance()
                if self._peek() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.EQ, "==", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.EQUALS, "=", start_line, start_col))
                continue

            if char == "!":
                self._advance()
                if self._peek() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.NEQ, "!=", start_line, start_col))
                else:
                    raise JockyLexerError("Expected '=' after '!' for not-equals operator", start_line, start_col, character="!")
                continue

            if char == ">":
                self._advance()
                if self._peek() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.GTE, ">=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.GT, ">", start_line, start_col))
                continue

            if char == "<":
                self._advance()
                if self._peek() == "=":
                    self._advance()
                    tokens.append(Token(TokenType.LTE, "<=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.LT, "<", start_line, start_col))
                continue

            if char == ",":
                self._advance()
                tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
                continue

            # 6. Identifiers, Keywords, Targets, Booleans
            if char.isalpha() or char == "_":
                ident_chars = []
                while self.position < self.length:
                    c = self._peek()
                    if c is not None and (c.isalnum() or c == "_"):
                        ident_chars.append(self._advance())
                    else:
                        break

                ident_str = "".join(ident_chars)
                lower_ident = ident_str.lower()

                # Check for boolean literals
                if lower_ident == "true":
                    tokens.append(Token(TokenType.BOOLEAN, True, start_line, start_col))
                elif lower_ident == "false":
                    tokens.append(Token(TokenType.BOOLEAN, False, start_line, start_col))
                elif lower_ident in KEYWORDS:
                    tokens.append(Token(KEYWORDS[lower_ident], lower_ident, start_line, start_col))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, ident_str, start_line, start_col))
                continue

            # 7. Unrecognized character
            bad_char = self._advance()
            raise JockyLexerError(
                f"Unexpected character '{bad_char}'",
                start_line,
                start_col,
                character=bad_char,
            )

        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens
