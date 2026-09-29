from app.jocky import (
    tokenize_jocky,
    parse_jocky,
    compile_jocky,
    TokenType,
    Program,
    ScanStatement,
    CollectStatement,
    HashStatement,
    FlagStatement,
    ReportStatement,
)


def test_complete_end_to_end_pipeline():
    source = """
    # 1. Look for unverified processes
    scan processes
    where signed == false
    and network_connections > 0

    # 2. Gather persistence artifacts
    collect autoruns, scheduled_tasks, services

    # 3. Hash files in suspicious staging directories
    hash files in "%TEMP%"
    check against reputation

    # 4. Trigger alert on unsigned binaries
    flag when signed == false
    severity = high

    # 5. Route results to centralized management server
    report to server
    """

    # 1. Tokenization Stage
    tokens = tokenize_jocky(source)
    assert len(tokens) > 10
    assert tokens[0].type == TokenType.SCAN
    assert tokens[-1].type == TokenType.EOF

    # 2. Parsing Stage -> Strongly-Typed AST
    ast = parse_jocky(source)
    assert isinstance(ast, Program)
    assert len(ast.statements) == 5
    assert isinstance(ast.statements[0], ScanStatement)
    assert isinstance(ast.statements[1], CollectStatement)
    assert isinstance(ast.statements[2], HashStatement)
    assert isinstance(ast.statements[3], FlagStatement)
    assert isinstance(ast.statements[4], ReportStatement)

    # 3. Execution Plan Compilation Stage -> Deterministic JSON-compatible dict
    plan = compile_jocky(source)
    assert plan["version"] == "1"
    assert len(plan["statements"]) == 5

    # Statement 1: Scan
    stmt0 = plan["statements"][0]
    assert stmt0["operation"] == "scan"
    assert stmt0["target"] == "processes"
    assert stmt0["where"]["operator"] == "and"
    assert len(stmt0["where"]["conditions"]) == 2

    # Statement 2: Collect
    stmt1 = plan["statements"][1]
    assert stmt1["operation"] == "collect"
    assert stmt1["targets"] == ["autoruns", "scheduled_tasks", "services"]

    # Statement 3: Hash
    stmt2 = plan["statements"][2]
    assert stmt2["operation"] == "hash"
    assert stmt2["path"] == "%TEMP%"
    assert stmt2["check_against"] == "reputation"

    # Statement 4: Flag
    stmt3 = plan["statements"][3]
    assert stmt3["operation"] == "flag"
    assert stmt3["severity"] == "high"

    # Statement 5: Report
    stmt4 = plan["statements"][4]
    assert stmt4["operation"] == "report"
    assert stmt4["destination"] == "server"
