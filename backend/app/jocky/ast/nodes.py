from dataclasses import dataclass, field
from typing import List, Optional, Any, Union, Dict


@dataclass
class ASTNode:
    """Base class for all typed JOCKY AST nodes."""
    line: int = 1
    column: int = 1


@dataclass
class Literal(ASTNode):
    """Represents a literal constant (string, boolean, number)."""
    value: Any = None


@dataclass
class Identifier(ASTNode):
    """Represents an identifier/field reference."""
    name: str = ""


# --- Conditions ---

@dataclass
class Condition(ASTNode):
    """Base class for condition expressions."""
    pass


@dataclass
class Comparison(Condition):
    """
    Represents a simple comparison expression.
    e.g. `signed == false`, `network_connections > 0`, `name contains "malware"`
    """
    field: str = ""
    operator: str = ""  # ==, !=, >, <, >=, <=, contains, in
    value: Any = None


@dataclass
class BinaryCondition(Condition):
    """
    Represents combined conditions using logical AND / OR.
    e.g. `signed == false and network_connections > 0`
    """
    left: Condition = field(default_factory=Condition)
    operator: str = "and"  # "and" | "or"
    right: Condition = field(default_factory=Condition)


# --- Statements ---

@dataclass
class Statement(ASTNode):
    """Base class for all JOCKY statements."""
    pass


@dataclass
class ScanStatement(Statement):
    """
    Represents a scan command.
    e.g. `scan processes where signed == false`
    """
    target: str = ""
    condition: Optional[Condition] = None


@dataclass
class CollectStatement(Statement):
    """
    Represents a forensic artifact collection command.
    e.g. `collect autoruns, scheduled_tasks, services`
    """
    targets: List[str] = field(default_factory=list)
    collector_type: str = ""
    filters: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.collector_type and not self.targets:
            self.targets = [self.collector_type]
        elif self.targets and not self.collector_type:
            self.collector_type = self.targets[0]


@dataclass
class HashStatement(Statement):
    """
    Represents a file hashing command.
    e.g. `hash files in "%TEMP%" check against reputation`
    """
    path: str = ""
    check_against: Optional[str] = None


@dataclass
class CheckStatement(Statement):
    """
    Represents a standalone reputation or signature check.
    e.g. `check against reputation`
    """
    target: str = ""
    engine: str = ""
    rule_identifier: str = ""
    target_field: str = ""


@dataclass
class FlagStatement(Statement):
    """
    Represents an alerting/flagging rule.
    e.g. `flag when signed == false severity = high`
    """
    condition: Condition = field(default_factory=Condition)
    severity: Optional[str] = None  # "low", "medium", "high", "critical"


@dataclass
class AlertStatement(Statement):
    """Alias for flagging/alerting node."""
    condition: Any = ""
    severity: str = "HIGH"
    message: str = ""


@dataclass
class TargetStatement(Statement):
    """Represents target filtering expression."""
    expression: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportStatement(Statement):
    """
    Represents an output destination specification.
    e.g. `report to console`, `report to server`
    """
    destination: str = ""  # "console" | "server"


@dataclass
class Program(ASTNode):
    """Root AST Node representing the complete parsed JOCKY script."""
    statements: List[Statement] = field(default_factory=list)


# Backward-compatible alias
ScriptAST = Program
