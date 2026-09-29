from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Keywords
    TARGET = auto()
    COLLECT = auto()
    WHERE = auto()
    FILTER = auto()
    CHECK = auto()
    ALERT = auto()
    SEVERITY = auto()
    MESSAGE = auto()
    WITH_HASH = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()

    # Literals & Identifiers
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()

    # Symbols & Operators
    EQUALS = auto()
    NOT_EQUALS = auto()
    GREATER_THAN = auto()
    LESS_THAN = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int
