from typing import List, Optional, Any, Set
from app.jocky.lexer.tokens import Token, TokenType
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
from app.jocky.errors import JockyParserError, JockyValidationError

VALID_TARGETS: Set[str] = {
    "processes",
    "connections",
    "files",
    "drivers",
    "services",
    "autoruns",
    "scheduled_tasks",
    "users",
    "sessions",
    "event_logs",
}

VALID_LEVELS: Set[str] = {
    "low",
    "medium",
    "high",
    "critical",
}

VALID_DESTINATIONS: Set[str] = {
    "console",
    "server",
}

COMPARISON_OPERATOR_TYPES: Set[TokenType] = {
    TokenType.EQ,
    TokenType.NEQ,
    TokenType.GT,
    TokenType.LT,
    TokenType.GTE,
    TokenType.LTE,
    TokenType.CONTAINS,
    TokenType.IN,
}

DISALLOWED_OFFENSIVE_VERBS: Set[str] = {
    "execute",
    "exec",
    "inject",
    "load",
    "unload",
    "disable",
    "download",
    "upload",
    "write",
    "modify",
    "delete",
    "kill",
    "shell",
    "spawn",
    "c2",
    "evade",
    "bypass",
}


class JockyParser:
    """
    Recursive-descent parser for JOCKY DSL.
    Transforms a stream of tokens into a strongly-typed AST (Program).
    """

    def __init__(self, tokens: Optional[List[Token]] = None):
        self.tokens: List[Token] = tokens or []
        self.cursor: int = 0

    def _peek(self, offset: int = 0) -> Token:
        pos = self.cursor + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1] if self.tokens else Token(TokenType.EOF, None, 1, 1)

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _advance(self) -> Token:
        token = self._peek()
        if not self._is_at_end():
            self.cursor += 1
        return token

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return token_type == TokenType.EOF
        return self._peek().type == token_type

    def _match(self, *token_types: TokenType) -> bool:
        for t in token_types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, expected_type: TokenType, error_message: str) -> Token:
        token = self._peek()
        if token.type == expected_type:
            return self._advance()
        actual_desc = f"'{token.value}' ({token.type.name})" if token.value is not None else token.type.name
        raise JockyParserError(
            message=error_message,
            line=token.line,
            column=token.column,
            expected=expected_type.name,
            actual=actual_desc,
        )

    def parse(self) -> Program:
        """Parses the full token stream into a Program node containing statements."""
        statements: List[Statement] = []

        if not self.tokens or (len(self.tokens) == 1 and self.tokens[0].type == TokenType.EOF):
            raise JockyParserError("Empty script: expected at least one statement", 1, 1, expected="STATEMENT", actual="EOF")

        while not self._is_at_end():
            stmt = self._parse_statement()
            statements.append(stmt)

        if not statements:
            tok = self._peek()
            raise JockyParserError("Expected at least one statement", tok.line, tok.column, expected="STATEMENT", actual=tok.type.name)

        return Program(statements=statements, line=statements[0].line, column=statements[0].column)

    def _parse_statement(self) -> Statement:
        tok = self._peek()

        # Check for disallowed offensive verbs explicitly
        if tok.type == TokenType.IDENTIFIER and isinstance(tok.value, str):
            verb_lower = tok.value.lower()
            if verb_lower in DISALLOWED_OFFENSIVE_VERBS:
                raise JockyValidationError(
                    f"Unsupported or disallowed offensive operation '{tok.value}'. JOCKY is strictly a read-only forensic DSL.",
                    line=tok.line,
                    column=tok.column,
                )

        if tok.type == TokenType.SCAN:
            return self._parse_scan_statement()
        elif tok.type == TokenType.COLLECT:
            return self._parse_collect_statement()
        elif tok.type == TokenType.HASH:
            return self._parse_hash_statement()
        elif tok.type == TokenType.CHECK:
            return self._parse_check_statement()
        elif tok.type == TokenType.FLAG:
            return self._parse_flag_statement()
        elif tok.type == TokenType.REPORT:
            return self._parse_report_statement()
        else:
            actual_desc = f"'{tok.value}'" if tok.value is not None else tok.type.name
            raise JockyParserError(
                f"Unexpected token '{tok.value or tok.type.name}' at start of statement. Expected 'scan', 'collect', 'hash', 'check', 'flag', or 'report'",
                line=tok.line,
                column=tok.column,
                expected="scan | collect | hash | check | flag | report",
                actual=actual_desc,
            )

    def _parse_scan_statement(self) -> ScanStatement:
        start_tok = self._consume(TokenType.SCAN, "Expected 'scan' keyword")
        target_tok = self._peek()

        # Target can be a specific target keyword or identifier
        target_name = self._extract_identifier_or_keyword_name(target_tok)
        if not target_name:
            raise JockyParserError(
                f"Expected forensic scan target after 'scan', got {target_tok.type.name}",
                line=target_tok.line,
                column=target_tok.column,
                expected="processes | connections | files | drivers | services | autoruns | scheduled_tasks | users | sessions | event_logs",
                actual=target_tok.type.name,
            )
        self._advance()

        target_clean = target_name.lower()
        if target_clean not in VALID_TARGETS:
            raise JockyParserError(
                f"Invalid scan target '{target_name}'. Valid targets are: {', '.join(sorted(VALID_TARGETS))}",
                line=target_tok.line,
                column=target_tok.column,
                expected=" | ".join(sorted(VALID_TARGETS)),
                actual=target_name,
            )

        condition: Optional[Condition] = None
        if self._check(TokenType.WHERE):
            self._advance()
            condition = self._parse_condition()

        return ScanStatement(target=target_clean, condition=condition, line=start_tok.line, column=start_tok.column)

    def _parse_collect_statement(self) -> CollectStatement:
        start_tok = self._consume(TokenType.COLLECT, "Expected 'collect' keyword")
        targets: List[str] = []

        first_tok = self._peek()
        first_name = self._extract_identifier_or_keyword_name(first_tok)
        if not first_name:
            raise JockyParserError(
                f"Expected target identifier after 'collect', got {first_tok.type.name}",
                line=first_tok.line,
                column=first_tok.column,
                expected="IDENTIFIER",
                actual=first_tok.type.name,
            )
        self._advance()
        targets.append(first_name.lower())

        while self._match(TokenType.COMMA):
            next_tok = self._peek()
            next_name = self._extract_identifier_or_keyword_name(next_tok)
            if not next_name:
                raise JockyParserError(
                    f"Expected target identifier after comma in 'collect' statement, got {next_tok.type.name}",
                    line=next_tok.line,
                    column=next_tok.column,
                    expected="IDENTIFIER",
                    actual=next_tok.type.name,
                )
            self._advance()
            targets.append(next_name.lower())

        return CollectStatement(targets=targets, line=start_tok.line, column=start_tok.column)

    def _parse_hash_statement(self) -> HashStatement:
        start_tok = self._consume(TokenType.HASH, "Expected 'hash' keyword")
        self._consume(TokenType.FILES, "Expected 'files' keyword after 'hash'")
        self._consume(TokenType.IN, "Expected 'in' keyword after 'files'")

        path_tok = self._peek()
        if path_tok.type not in (TokenType.STRING, TokenType.IDENTIFIER):
            raise JockyParserError(
                "Expected file path string after 'hash files in'",
                line=path_tok.line,
                column=path_tok.column,
                expected="STRING",
                actual=path_tok.type.name,
            )
        self._advance()
        path_value = str(path_tok.value)

        check_against: Optional[str] = None
        if self._check(TokenType.CHECK):
            self._advance()
            self._consume(TokenType.AGAINST, "Expected 'against' keyword after 'check'")
            against_tok = self._peek()
            against_name = self._extract_identifier_or_keyword_name(against_tok)
            if not against_name:
                raise JockyParserError(
                    "Expected identifier (e.g. 'reputation') after 'check against'",
                    line=against_tok.line,
                    column=against_tok.column,
                    expected="IDENTIFIER",
                    actual=against_tok.type.name,
                )
            self._advance()
            check_against = against_name.lower()

        return HashStatement(path=path_value, check_against=check_against, line=start_tok.line, column=start_tok.column)

    def _parse_check_statement(self) -> CheckStatement:
        start_tok = self._consume(TokenType.CHECK, "Expected 'check' keyword")
        self._consume(TokenType.AGAINST, "Expected 'against' keyword after 'check'")

        target_tok = self._peek()
        target_name = self._extract_identifier_or_keyword_name(target_tok)
        if not target_name:
            raise JockyParserError(
                "Expected identifier (e.g. 'reputation') after 'check against'",
                line=target_tok.line,
                column=target_tok.column,
                expected="IDENTIFIER",
                actual=target_tok.type.name,
            )
        self._advance()
        return CheckStatement(target=target_name.lower(), line=start_tok.line, column=start_tok.column)

    def _parse_flag_statement(self) -> FlagStatement:
        start_tok = self._consume(TokenType.FLAG, "Expected 'flag' keyword")
        self._consume(TokenType.WHEN, "Expected 'when' keyword after 'flag'")

        condition = self._parse_condition()
        severity: Optional[str] = None

        if self._check(TokenType.SEVERITY):
            self._advance()
            self._consume(TokenType.EQUALS, "Expected '=' after 'severity'")
            level_tok = self._peek()
            level_name = self._extract_identifier_or_keyword_name(level_tok)
            if not level_name or level_name.lower() not in VALID_LEVELS:
                raise JockyParserError(
                    f"Invalid severity level '{level_tok.value}'. Expected: {', '.join(sorted(VALID_LEVELS))}",
                    line=level_tok.line,
                    column=level_tok.column,
                    expected="low | medium | high | critical",
                    actual=str(level_tok.value),
                )
            self._advance()
            severity = level_name.lower()

        return FlagStatement(condition=condition, severity=severity, line=start_tok.line, column=start_tok.column)

    def _parse_report_statement(self) -> ReportStatement:
        start_tok = self._consume(TokenType.REPORT, "Expected 'report' keyword")
        self._consume(TokenType.TO, "Expected 'to' keyword after 'report'")

        dest_tok = self._peek()
        dest_name = self._extract_identifier_or_keyword_name(dest_tok)
        if not dest_name or dest_name.lower() not in VALID_DESTINATIONS:
            raise JockyParserError(
                f"Invalid report destination '{dest_tok.value}'. Expected: {', '.join(sorted(VALID_DESTINATIONS))}",
                line=dest_tok.line,
                column=dest_tok.column,
                expected="console | server",
                actual=str(dest_tok.value),
            )
        self._advance()
        return ReportStatement(destination=dest_name.lower(), line=start_tok.line, column=start_tok.column)

    # --- Condition & Expression Parsing ---

    def _parse_condition(self) -> Condition:
        expr = self._parse_comparison_expression()

        while self._check(TokenType.AND) or self._check(TokenType.OR):
            op_tok = self._advance()
            op_str = "and" if op_tok.type == TokenType.AND else "or"
            right_expr = self._parse_comparison_expression()
            expr = BinaryCondition(left=expr, operator=op_str, right=right_expr, line=op_tok.line, column=op_tok.column)

        return expr

    def _parse_comparison_expression(self) -> Comparison:
        field_tok = self._peek()
        field_name = self._extract_identifier_or_keyword_name(field_tok)
        if not field_name:
            raise JockyParserError(
                f"Expected field identifier in condition, got '{field_tok.value or field_tok.type.name}'",
                line=field_tok.line,
                column=field_tok.column,
                expected="IDENTIFIER",
                actual=field_tok.type.name,
            )
        self._advance()

        op_tok = self._peek()
        operator_str = self._extract_operator(op_tok)
        if not operator_str:
            raise JockyParserError(
                f"Expected comparison operator (==, !=, >, <, >=, <=, contains, in), got '{op_tok.value or op_tok.type.name}'",
                line=op_tok.line,
                column=op_tok.column,
                expected="== | != | > | < | >= | <= | contains | in",
                actual=str(op_tok.value or op_tok.type.name),
            )
        self._advance()

        val_tok = self._peek()
        if val_tok.type in (TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN):
            self._advance()
            val_value = val_tok.value
        else:
            ident_val = self._extract_identifier_or_keyword_name(val_tok)
            if ident_val is not None:
                self._advance()
                val_value = ident_val
            else:
                raise JockyParserError(
                    f"Expected literal value (string, number, boolean, identifier) in condition, got '{val_tok.value or val_tok.type.name}'",
                    line=val_tok.line,
                    column=val_tok.column,
                    expected="LITERAL",
                    actual=val_tok.type.name,
                )

        return Comparison(
            field=field_name,
            operator=operator_str,
            value=val_value,
            line=field_tok.line,
            column=field_tok.column,
        )

    def _extract_identifier_or_keyword_name(self, tok: Token) -> Optional[str]:
        if tok.type == TokenType.IDENTIFIER:
            return str(tok.value)
        # Contextual keywords or targets can also serve as identifiers/targets
        if tok.type in (
            TokenType.PROCESSES,
            TokenType.CONNECTIONS,
            TokenType.SERVICES,
            TokenType.AUTORUNS,
            TokenType.SCHEDULED_TASKS,
            TokenType.DRIVERS,
            TokenType.USERS,
            TokenType.SESSIONS,
            TokenType.EVENT_LOGS,
            TokenType.REPUTATION,
            TokenType.FILES,
        ):
            return str(tok.value)
        return None

    def _extract_operator(self, tok: Token) -> Optional[str]:
        op_map = {
            TokenType.EQ: "==",
            TokenType.NEQ: "!=",
            TokenType.GT: ">",
            TokenType.LT: "<",
            TokenType.GTE: ">=",
            TokenType.LTE: "<=",
            TokenType.CONTAINS: "contains",
            TokenType.IN: "in",
        }
        if tok.type in op_map:
            return op_map[tok.type]
        if tok.type == TokenType.IDENTIFIER and isinstance(tok.value, str):
            # Support custom comparison verbs like injected_into
            val_lower = tok.value.lower()
            if val_lower in ("contains", "in", "injected_into", "matches", "like"):
                return val_lower
        return None
