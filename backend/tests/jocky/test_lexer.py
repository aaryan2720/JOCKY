import pytest
from app.jocky.lexer import JockyLexer, TokenType
from app.jocky.errors import JockyLexerError


def test_tokenize_basic_keywords():
    source = "scan collect hash files in check against flag when severity report to where and or"
    lexer = JockyLexer(source)
    tokens = lexer.tokenize()
    
    expected_types = [
        TokenType.SCAN,
        TokenType.COLLECT,
        TokenType.HASH,
        TokenType.FILES,
        TokenType.IN,
        TokenType.CHECK,
        TokenType.AGAINST,
        TokenType.FLAG,
        TokenType.WHEN,
        TokenType.SEVERITY,
        TokenType.REPORT,
        TokenType.TO,
        TokenType.WHERE,
        TokenType.AND,
        TokenType.OR,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected_types


def test_tokenize_operators():
    source = "== != > < >= <= contains in ="
    lexer = JockyLexer(source)
    tokens = lexer.tokenize()

    expected_types = [
        TokenType.EQ,
        TokenType.NEQ,
        TokenType.GT,
        TokenType.LT,
        TokenType.GTE,
        TokenType.LTE,
        TokenType.CONTAINS,
        TokenType.IN,
        TokenType.EQUALS,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected_types


def test_tokenize_literals_and_comments():
    source = """
    # Forensic process scan
    signed == false
    network_connections > 5
    path == "C:\\\\Windows\\\\System32"
    ratio <= 3.14
    """
    lexer = JockyLexer(source)
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].value == "signed"
    assert tokens[1].type == TokenType.EQ
    assert tokens[2].type == TokenType.BOOLEAN
    assert tokens[2].value is False

    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[3].value == "network_connections"
    assert tokens[4].type == TokenType.GT
    assert tokens[5].type == TokenType.NUMBER
    assert tokens[5].value == 5

    assert tokens[6].type == TokenType.IDENTIFIER
    assert tokens[6].value == "path"
    assert tokens[7].type == TokenType.EQ
    assert tokens[8].type == TokenType.STRING
    assert tokens[8].value == "C:\\Windows\\System32"

    assert tokens[9].type == TokenType.IDENTIFIER
    assert tokens[9].value == "ratio"
    assert tokens[10].type == TokenType.LTE
    assert tokens[11].type == TokenType.NUMBER
    assert tokens[11].value == 3.14


def test_lexer_line_and_column_tracking():
    source = "scan processes\nwhere signed == false"
    lexer = JockyLexer(source)
    tokens = lexer.tokenize()

    assert tokens[0].line == 1
    assert tokens[0].column == 1
    assert tokens[1].line == 1
    assert tokens[1].column == 6

    # 'where' on line 2, column 1
    assert tokens[2].line == 2
    assert tokens[2].column == 1
    assert tokens[3].line == 2
    assert tokens[3].column == 7


def test_lexer_unclosed_string_error():
    source = 'scan files where path == "C:\\unclosed'
    lexer = JockyLexer(source)
    with pytest.raises(JockyLexerError) as exc_info:
        lexer.tokenize()
    assert "Unclosed string literal" in str(exc_info.value)
    assert exc_info.value.line == 1


def test_lexer_unexpected_character_error():
    source = "scan processes @ 123"
    lexer = JockyLexer(source)
    with pytest.raises(JockyLexerError) as exc_info:
        lexer.tokenize()
    assert "Unexpected character '@'" in str(exc_info.value)
    assert exc_info.value.column == 16
    assert exc_info.value.character == "@"
