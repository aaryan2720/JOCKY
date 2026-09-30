import re
from typing import List
from app.jocky.lexer.tokens import Token, TokenType

KEYWORDS = {
    "TARGET": TokenType.TARGET,
    "COLLECT": TokenType.COLLECT,
    "SCAN": TokenType.COLLECT,
    "WHERE": TokenType.WHERE,
    "FILTER": TokenType.FILTER,
    "CHECK": TokenType.CHECK,
    "ALERT": TokenType.ALERT,
    "FLAG": TokenType.ALERT,
    "SEVERITY": TokenType.SEVERITY,
    "MESSAGE": TokenType.MESSAGE,
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "NOT": TokenType.NOT,
    "IN": TokenType.IN,
}


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
        """Tokenize source string into Token list ending with EOF."""
        tokens: List[Token] = []
        if not self.source or not self.source.strip():
            return [Token(type=TokenType.EOF, value=None, line=self.line, column=self.column)]

        lines = self.source.splitlines(keepends=True)
        for line_num, line_str in enumerate(lines, start=1):
            col = 1
            idx = 0
            while idx < len(line_str):
                ch = line_str[idx]

                # Whitespace
                if ch.isspace():
                    idx += 1
                    col += 1
                    continue

                # Comments
                if ch == "#":
                    break

                # Semicolon
                if ch == ";":
                    tokens.append(Token(type=TokenType.SEMICOLON, value=";", line=line_num, column=col))
                    idx += 1
                    col += 1
                    continue

                # Strings
                if ch in ("'", '"'):
                    quote = ch
                    start_col = col
                    str_val = []
                    idx += 1
                    col += 1
                    while idx < len(line_str) and line_str[idx] != quote:
                        str_val.append(line_str[idx])
                        idx += 1
                        col += 1
                    if idx < len(line_str) and line_str[idx] == quote:
                        idx += 1
                        col += 1
                    tokens.append(Token(type=TokenType.STRING, value="".join(str_val), line=line_num, column=start_col))
                    continue

                # Symbols: ==, !=, <=, >=, <, >
                if line_str[idx : idx + 2] in ("==", "!=", "<=", ">="):
                    sym = line_str[idx : idx + 2]
                    tok_type = TokenType.EQUALS if sym == "==" else (TokenType.NOT_EQUALS if sym == "!=" else TokenType.IDENTIFIER)
                    tokens.append(Token(type=tok_type, value=sym, line=line_num, column=col))
                    idx += 2
                    col += 2
                    continue

                if ch in ("(", ")", ",", "{", "}"):
                    tok_type = TokenType.LPAREN if ch == "(" else (TokenType.RPAREN if ch == ")" else TokenType.COMMA)
                    tokens.append(Token(type=tok_type, value=ch, line=line_num, column=col))
                    idx += 1
                    col += 1
                    continue

                # Numbers
                num_match = re.match(r"^\d+", line_str[idx:])
                if num_match:
                    num_str = num_match.group(0)
                    tokens.append(Token(type=TokenType.NUMBER, value=int(num_str), line=line_num, column=col))
                    idx += len(num_str)
                    col += len(num_str)
                    continue

                # Identifiers & Keywords
                word_match = re.match(r"^[a-zA-Z_][a-zA-Z0-9_\.]*", line_str[idx:])
                if word_match:
                    word = word_match.group(0)
                    upper = word.upper()
                    if upper in KEYWORDS:
                        tokens.append(Token(type=KEYWORDS[upper], value=word, line=line_num, column=col))
                    elif upper in ("TRUE", "FALSE"):
                        tokens.append(Token(type=TokenType.BOOLEAN, value=(upper == "TRUE"), line=line_num, column=col))
                    else:
                        tokens.append(Token(type=TokenType.IDENTIFIER, value=word, line=line_num, column=col))
                    idx += len(word)
                    col += len(word)
                    continue

                # Other characters
                tokens.append(Token(type=TokenType.IDENTIFIER, value=ch, line=line_num, column=col))
                idx += 1
                col += 1

        tokens.append(Token(type=TokenType.EOF, value=None, line=self.line, column=self.column))
        return tokens

