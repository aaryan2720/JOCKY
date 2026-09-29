from app.jocky.lexer import JockyLexer, TokenType
from app.jocky.parser import JockyParser
from app.jocky.ast import Program, ScanStatement
from app.jocky.interpreter import JockyInterpreter
from app.jocky.planner import JockyPlanner


def test_jocky_lexer_basic():
    lexer = JockyLexer("scan processes")
    tokens = lexer.tokenize()
    assert len(tokens) == 3
    assert tokens[0].type == TokenType.SCAN
    assert tokens[1].type == TokenType.PROCESSES
    assert tokens[2].type == TokenType.EOF


def test_jocky_parser_basic():
    lexer = JockyLexer("scan processes")
    tokens = lexer.tokenize()
    parser = JockyParser(tokens)
    ast = parser.parse()
    assert isinstance(ast, Program)
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], ScanStatement)
    assert ast.statements[0].target == "processes"


def test_jocky_planner_basic():
    lexer = JockyLexer("scan processes where signed == false")
    tokens = lexer.tokenize()
    parser = JockyParser(tokens)
    ast = parser.parse()
    planner = JockyPlanner(ast)
    plan = planner.build_execution_plan()
    assert plan["version"] == "1"
    assert len(plan["statements"]) == 1
    assert plan["statements"][0]["operation"] == "scan"
