import pytest
from app.jocky.parser import JockyParser
from app.jocky.lexer import JockyLexer
from app.jocky.ast.nodes import (
    Program,
    ScanStatement,
    CollectStatement,
    HashStatement,
    CheckStatement,
    FlagStatement,
    ReportStatement,
    Comparison,
    BinaryCondition,
)
from app.jocky.errors import JockyParserError


def parse(source: str) -> Program:
    tokens = JockyLexer(source).tokenize()
    return JockyParser(tokens).parse()


def test_parse_basic_scan():
    prog = parse("scan processes")
    assert len(prog.statements) == 1
    stmt = prog.statements[0]
    assert isinstance(stmt, ScanStatement)
    assert stmt.target == "processes"
    assert stmt.condition is None


def test_parse_scan_with_where():
    prog = parse("scan processes where signed == false")
    assert len(prog.statements) == 1
    stmt = prog.statements[0]
    assert isinstance(stmt, ScanStatement)
    assert stmt.target == "processes"
    assert isinstance(stmt.condition, Comparison)
    assert stmt.condition.field == "signed"
    assert stmt.condition.operator == "=="
    assert stmt.condition.value is False


def test_parse_scan_with_and_conditions():
    source = """
    scan processes
    where signed == false
    and network_connections > 0
    """
    prog = parse(source)
    stmt = prog.statements[0]
    assert isinstance(stmt, ScanStatement)
    assert isinstance(stmt.condition, BinaryCondition)
    assert stmt.condition.operator == "and"
    assert isinstance(stmt.condition.left, Comparison)
    assert stmt.condition.left.field == "signed"
    assert isinstance(stmt.condition.right, Comparison)
    assert stmt.condition.right.field == "network_connections"
    assert stmt.condition.right.operator == ">"
    assert stmt.condition.right.value == 0


def test_parse_scan_with_or_conditions():
    source = 'scan connections where remote_port == 4444 or remote_port == 1337'
    prog = parse(source)
    stmt = prog.statements[0]
    assert isinstance(stmt, ScanStatement)
    assert isinstance(stmt.condition, BinaryCondition)
    assert stmt.condition.operator == "or"
    assert stmt.condition.left.value == 4444
    assert stmt.condition.right.value == 1337


def test_parse_collect_multiple_targets():
    source = "collect autoruns, scheduled_tasks, services"
    prog = parse(source)
    assert len(prog.statements) == 1
    stmt = prog.statements[0]
    assert isinstance(stmt, CollectStatement)
    assert stmt.targets == ["autoruns", "scheduled_tasks", "services"]


def test_parse_hash_statement_basic():
    source = 'hash files in "%TEMP%"'
    prog = parse(source)
    assert len(prog.statements) == 1
    stmt = prog.statements[0]
    assert isinstance(stmt, HashStatement)
    assert stmt.path == "%TEMP%"
    assert stmt.check_against is None


def test_parse_hash_statement_with_check():
    source = 'hash files in "/tmp" check against reputation'
    prog = parse(source)
    assert len(prog.statements) == 1
    stmt = prog.statements[0]
    assert isinstance(stmt, HashStatement)
    assert stmt.path == "/tmp"
    assert stmt.check_against == "reputation"


def test_parse_check_standalone():
    source = "check against reputation"
    prog = parse(source)
    assert len(prog.statements) == 1
    stmt = prog.statements[0]
    assert isinstance(stmt, CheckStatement)
    assert stmt.target == "reputation"


def test_parse_flag_with_severity():
    source = """
    flag when signed == false
    severity = high
    """
    prog = parse(source)
    assert len(prog.statements) == 1
    stmt = prog.statements[0]
    assert isinstance(stmt, FlagStatement)
    assert isinstance(stmt.condition, Comparison)
    assert stmt.condition.field == "signed"
    assert stmt.severity == "high"


def test_parse_report():
    prog1 = parse("report to console")
    assert isinstance(prog1.statements[0], ReportStatement)
    assert prog1.statements[0].destination == "console"

    prog2 = parse("report to server")
    assert isinstance(prog2.statements[0], ReportStatement)
    assert prog2.statements[0].destination == "server"


def test_parse_multiple_statements():
    source = """
    # Multi-step investigation
    scan processes where signed == false
    collect autoruns, services
    hash files in "%TEMP%" check against reputation
    flag when signed == false severity = critical
    report to server
    """
    prog = parse(source)
    assert len(prog.statements) == 5
    assert isinstance(prog.statements[0], ScanStatement)
    assert isinstance(prog.statements[1], CollectStatement)
    assert isinstance(prog.statements[2], HashStatement)
    assert isinstance(prog.statements[3], FlagStatement)
    assert isinstance(prog.statements[4], ReportStatement)


def test_parser_invalid_target_error():
    source = "scan invalid_target_name"
    with pytest.raises(JockyParserError) as exc_info:
        parse(source)
    assert "Invalid scan target 'invalid_target_name'" in str(exc_info.value)
    assert exc_info.value.line == 1


def test_parser_invalid_severity_error():
    source = "flag when signed == false severity = extreme"
    with pytest.raises(JockyParserError) as exc_info:
        parse(source)
    assert "Invalid severity level 'extreme'" in str(exc_info.value)


def test_parser_invalid_destination_error():
    source = "report to email"
    with pytest.raises(JockyParserError) as exc_info:
        parse(source)
    assert "Invalid report destination 'email'" in str(exc_info.value)


def test_parser_missing_tokens_error():
    source = "scan"
    with pytest.raises(JockyParserError) as exc_info:
        parse(source)
    assert "Expected forensic scan target after 'scan'" in str(exc_info.value)
    assert exc_info.value.line == 1
