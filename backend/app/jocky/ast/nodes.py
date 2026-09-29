from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


class ASTNode:
    """Base node for all JOCKY AST elements."""
    pass


@dataclass
class TargetStatement(ASTNode):
    """Represents a TARGET filter clause (e.g. TARGET os == 'windows')."""
    expression: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectStatement(ASTNode):
    """Represents a COLLECT clause (e.g. COLLECT processes WHERE ...)."""
    collector_type: str = ""
    filters: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckStatement(ASTNode):
    """Represents a CHECK clause (e.g. CHECK yara RULE ...)."""
    engine: str = ""
    rule_identifier: str = ""
    target_field: Optional[str] = None


@dataclass
class AlertStatement(ASTNode):
    """Represents an ALERT trigger condition."""
    condition: str = ""
    severity: str = "MEDIUM"
    message: str = ""


@dataclass
class ScriptAST(ASTNode):
    """Root AST Node representing an entire parsed JOCKY script."""
    statements: List[ASTNode] = field(default_factory=list)
