from app.jocky.lexer import JockyLexer, TokenType
from app.jocky.parser import JockyParser
from app.jocky.ast import ScriptAST
from app.jocky.interpreter import JockyInterpreter
from app.jocky.planner import JockyPlanner


def test_jocky_lexer_stub():
    lexer = JockyLexer("COLLECT processes")
    tokens = lexer.tokenize()
    assert len(tokens) >= 1
    assert tokens[-1].type == TokenType.EOF


def test_jocky_parser_stub():
    parser = JockyParser()
    ast = parser.parse()
    assert isinstance(ast, ScriptAST)
    assert isinstance(ast.statements, list)


def test_jocky_planner_stub():
    ast = ScriptAST()
    planner = JockyPlanner(ast)
    plan = planner.build_execution_plan()
    assert "plan_version" in plan
    assert "collectors" in plan
