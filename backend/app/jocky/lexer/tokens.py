from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Keywords
    SCAN = auto()
    COLLECT = auto()
    HASH = auto()
    FILES = auto()
    IN = auto()
    CHECK = auto()
    AGAINST = auto()
    FLAG = auto()
    WHEN = auto()
    SEVERITY = auto()
    REPORT = auto()
    TO = auto()
    WHERE = auto()
    AND = auto()
    OR = auto()

    # Targets & Destination & Severity identifiers / keywords
    PROCESSES = auto()
    CONNECTIONS = auto()
    SERVICES = auto()
    AUTORUNS = auto()
    SCHEDULED_TASKS = auto()
    DRIVERS = auto()
    USERS = auto()
    SESSIONS = auto()
    EVENT_LOGS = auto()
    REPUTATION = auto()

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NUMBER = auto()

    # Operators
    EQ = auto()          # ==
    NEQ = auto()         # !=
    GT = auto()          # >
    LT = auto()          # <
    GTE = auto()         # >=
    LTE = auto()         # <=
    CONTAINS = auto()    # contains
    # IN is in keywords and doubles as operator

    # Punctuation
    COMMA = auto()       # ,
    EQUALS = auto()      # =

    # Special
    EOF = auto()


KEYWORDS = {
    "scan": TokenType.SCAN,
    "collect": TokenType.COLLECT,
    "hash": TokenType.HASH,
    "files": TokenType.FILES,
    "in": TokenType.IN,
    "check": TokenType.CHECK,
    "against": TokenType.AGAINST,
    "flag": TokenType.FLAG,
    "when": TokenType.WHEN,
    "severity": TokenType.SEVERITY,
    "report": TokenType.REPORT,
    "to": TokenType.TO,
    "where": TokenType.WHERE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "contains": TokenType.CONTAINS,
    # Targets / Context Keywords
    "processes": TokenType.PROCESSES,
    "connections": TokenType.CONNECTIONS,
    "services": TokenType.SERVICES,
    "autoruns": TokenType.AUTORUNS,
    "scheduled_tasks": TokenType.SCHEDULED_TASKS,
    "drivers": TokenType.DRIVERS,
    "users": TokenType.USERS,
    "sessions": TokenType.SESSIONS,
    "event_logs": TokenType.EVENT_LOGS,
    "reputation": TokenType.REPUTATION,
}


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"
