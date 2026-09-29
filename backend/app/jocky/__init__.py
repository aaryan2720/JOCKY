from typing import Dict, Any, List, Optional
from app.jocky.lexer.tokens import Token, TokenType
from app.jocky.lexer.lexer import JockyLexer
from app.jocky.ast.nodes import (
    Program,
    Statement,
    ScanStatement,
    CollectStatement,
    HashStatement,
    CheckStatement,
    FlagStatement,
    ReportStatement,
    Condition,
    Comparison,
    BinaryCondition,
)
from app.jocky.parser.parser import JockyParser
from app.jocky.interpreter.interpreter import JockyInterpreter
from app.jocky.planner.planner import JockyPlanner
from app.jocky.errors import (
    JockyError,
    JockyLexerError,
    JockyParserError,
    JockyValidationError,
)


def tokenize_jocky(source: str) -> List[Token]:
    """Tokenizes JOCKY DSL source code into a list of Tokens."""
    lexer = JockyLexer(source)
    return lexer.tokenize()


def parse_jocky(source: str) -> Program:
    """Tokenizes and parses JOCKY DSL source code into a strongly-typed AST (Program)."""
    tokens = tokenize_jocky(source)
    parser = JockyParser(tokens)
    return parser.parse()


def compile_jocky(source: str) -> Dict[str, Any]:
    """
    End-to-end compiler for JOCKY DSL.
    Transforms raw source code into a JSON-compatible execution plan.
    Pipeline: Source -> Lexer -> Parser -> AST -> Planner -> Execution Plan.
    """
    ast = parse_jocky(source)
    planner = JockyPlanner(ast)
    return planner.build_execution_plan()


def compile_jocky_to_json(source: str, indent: int = 2) -> str:
    """Compiles JOCKY DSL source code directly to a formatted JSON string."""
    ast = parse_jocky(source)
    planner = JockyPlanner(ast)
    return planner.to_json(indent=indent)


__all__ = [
    # Top-level API
    "tokenize_jocky",
    "parse_jocky",
    "compile_jocky",
    "compile_jocky_to_json",
    # Pipeline classes
    "JockyLexer",
    "JockyParser",
    "JockyInterpreter",
    "JockyPlanner",
    # AST Nodes
    "Program",
    "Statement",
    "ScanStatement",
    "CollectStatement",
    "HashStatement",
    "CheckStatement",
    "FlagStatement",
    "ReportStatement",
    "Condition",
    "Comparison",
    "BinaryCondition",
    # Tokens
    "Token",
    "TokenType",
    # Errors
    "JockyError",
    "JockyLexerError",
    "JockyParserError",
    "JockyValidationError",
]
