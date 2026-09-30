import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app
from app.jocky.lexer import JockyLexer, TokenType
from app.jocky.parser import JockyParser
from app.jocky.ast import (
    ScriptAST,
    CollectStatement,
    CheckStatement,
    AlertStatement,
    TargetStatement,
)
from app.jocky.planner import JockyPlanner
from app.detection.rules.flag_condition import evaluate_condition_predicate


# --- 1. Lexer & Tokenizer Tests ---

def test_lexer_keywords_and_punctuation():
    script = "COLLECT processes WHERE pid == 1004; CHECK yara(rule: 'cobalt'); FLAG signed == false; REPORT json;"
    lexer = JockyLexer(script)
    tokens = lexer.tokenize()
    assert len(tokens) >= 1
    assert tokens[-1].type == TokenType.EOF


def test_lexer_empty_script():
    lexer = JockyLexer("")
    tokens = lexer.tokenize()
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF


def test_lexer_whitespace_and_comments():
    script = "   \n\t  # comment line\nCOLLECT autoruns;"
    lexer = JockyLexer(script)
    tokens = lexer.tokenize()
    assert len(tokens) >= 1
    assert tokens[-1].type == TokenType.EOF


# --- 2. AST Construction Tests ---

def test_ast_target_statement():
    node = TargetStatement(expression={"os": "windows", "arch": "amd64"})
    assert node.expression["os"] == "windows"
    assert node.expression["arch"] == "amd64"


def test_ast_collect_statement():
    node = CollectStatement(
        collector_type="scheduled_tasks",
        filters={"enabled": True},
        options={"depth": 2},
    )
    assert node.collector_type == "scheduled_tasks"
    assert node.filters["enabled"] is True
    assert node.options["depth"] == 2


def test_ast_check_statement():
    node = CheckStatement(
        engine="yara",
        rule_identifier="cobalt_strike",
        target_field="path",
    )
    assert node.engine == "yara"
    assert node.rule_identifier == "cobalt_strike"
    assert node.target_field == "path"


def test_ast_alert_statement():
    node = AlertStatement(
        condition="signed == false",
        severity="HIGH",
        message="Unsigned executable detected",
    )
    assert node.severity == "HIGH"
    assert "Unsigned" in node.message


def test_ast_script_root():
    ast = ScriptAST(statements=[
        CollectStatement(collector_type="users"),
        CollectStatement(collector_type="sessions"),
    ])
    assert len(ast.statements) == 2


# --- 3. Parser Tests ---

def test_parser_empty_tokens():
    parser = JockyParser([])
    ast = parser.parse()
    assert isinstance(ast, ScriptAST)
    assert len(ast.statements) == 0


def test_parser_with_tokens():
    lexer = JockyLexer("COLLECT processes;")
    tokens = lexer.tokenize()
    parser = JockyParser(tokens)
    ast = parser.parse()
    assert isinstance(ast, ScriptAST)


# --- 4. Planner Tests ---

def test_planner_plan_structure():
    ast = ScriptAST(statements=[CollectStatement(collector_type="autoruns")])
    planner = JockyPlanner(ast)
    plan = planner.build_execution_plan()
    assert plan["plan_version"] == "1.0"
    assert "collectors" in plan
    assert "checks" in plan


# --- 5. Predicate Operator Tests ---

def test_predicate_equality_booleans():
    assert evaluate_condition_predicate(True, "eq", True) is True
    assert evaluate_condition_predicate(False, "eq", False) is True
    assert evaluate_condition_predicate(True, "==", False) is False
    assert evaluate_condition_predicate("true", "equals", True) is True
    assert evaluate_condition_predicate("false", "eq", False) is True


def test_predicate_inequality_booleans():
    assert evaluate_condition_predicate(True, "neq", False) is True
    assert evaluate_condition_predicate(False, "!=", True) is True
    assert evaluate_condition_predicate(True, "not_equals", True) is False


def test_predicate_string_containment():
    assert evaluate_condition_predicate("C:\\Windows\\System32\\cmd.exe", "contains", "cmd") is True
    assert evaluate_condition_predicate("powershell.exe", "in", "cobalt") is False
    assert evaluate_condition_predicate(["admin", "root"], "in", "root") is True
    assert evaluate_condition_predicate(None, "contains", "test") is False


def test_predicate_prefixes_and_suffixes():
    assert evaluate_condition_predicate("/usr/bin/bash", "startswith", "/usr") is True
    assert evaluate_condition_predicate("malware.scr", "endswith", ".scr") is True
    assert evaluate_condition_predicate("malware.exe", "endswith", ".scr") is False
    assert evaluate_condition_predicate(None, "startswith", "test") is False
    assert evaluate_condition_predicate(None, "endswith", "test") is False


def test_predicate_regex_valid_and_invalid():
    assert evaluate_condition_predicate("mimikatz v2.2", "regex", r"mimi(katz)?") is True
    assert evaluate_condition_predicate("clean_file.txt", "matches", r"^mimi") is False
    assert evaluate_condition_predicate(None, "regex", r".*") is False
    with pytest.raises(ValueError, match="Invalid regular expression"):
        evaluate_condition_predicate("test", "regex", r"[a-z(")


def test_predicate_numeric_comparisons():
    assert evaluate_condition_predicate(8080, "gt", 1024) is True
    assert evaluate_condition_predicate(1024, ">", 8080) is False
    assert evaluate_condition_predicate(443, "gte", 443) is True
    assert evaluate_condition_predicate(80, "lt", 443) is True
    assert evaluate_condition_predicate(80, "<=", 80) is True
    assert evaluate_condition_predicate("invalid", "gt", 10) is False


def test_predicate_unsupported_operator():
    with pytest.raises(ValueError, match="Unsupported condition operator"):
        evaluate_condition_predicate("foo", "os_system", "bar")


# --- 6. API Route Lifecycle Tests ---

@pytest.mark.asyncio
async def test_api_agents_route_lifecycle():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Register agent
        reg_payload = {
            "token": "jocky-agent-insecure-dev-token",
            "hostname": "PROD-SRV-99",
            "os": "windows",
            "arch": "amd64",
            "agent_version": "0.1.0",
        }
        resp = await client.post("/api/v1/agents/register", json=reg_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "agent_id" in data
        assert data["status"] == "enrolled"

        # List agents
        list_resp = await client.get("/api/v1/agents")
        assert list_resp.status_code == 200
        assert "items" in list_resp.json()


@pytest.mark.asyncio
async def test_api_jobs_route_lifecycle():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Create job
        job_payload = {
            "script_id": "script-pers-001",
            "target_agent_ids": ["agent-test-1"],
            "target_tags": ["finance"],
        }
        resp = await client.post("/api/v1/jobs", json=job_payload)
        assert resp.status_code == 202
        job_data = resp.json()
        assert "job_id" in job_data
        assert job_data["status"] == "queued"


@pytest.mark.asyncio
async def test_api_scripts_validation_route():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        validate_payload = {
            "body": "COLLECT autoruns; COLLECT users; COLLECT sessions;"
        }
        resp = await client.post("/api/v1/scripts/validate", json=validate_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
