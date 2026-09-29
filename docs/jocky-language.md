# JOCKY Forensic Domain-Specific Language (DSL) Specification

## 1. Overview & Purpose

**JOCKY** is a programmable, read-only forensic interrogation DSL engineered for Digital Forensics and Incident Response (DFIR) teams. It enables incident responders, threat hunters, and security analysts to declare unambiguous forensic queries that compile deterministically into structured JSON execution plans.

For the Hackathon MVP (Phase 1), JOCKY uses an in-memory **interpreted pipeline**:
```
Source Code (.jky)
       │
       ▼
   JockyLexer (Token Stream)
       │
       ▼
   JockyParser (Strongly-Typed AST)
       │
       ▼
 JockyInterpreter (Intermediate Representation)
       │
       ▼
  JockyPlanner (Deterministic JSON Execution Plan)
```

> [!NOTE]
> **Roadmap Note**: LLVM / native bytecode compilation is an item on the post-hackathon roadmap. The current MVP implementation delivers an interpreted pipeline producing stable JSON execution plans.

---

## 2. Design Philosophy & Safety Guarantee

JOCKY is designed with **zero offensive capability** and **strict read-only safety**:
- **Read-Only Telemetry**: JOCKY inspects existing forensic artifacts (process lists, network sockets, autoruns, services, logs, and file hashes).
- **No Side-Effects**: It cannot modify files, load drivers, kill processes, execute arbitrary shell commands, inject code, disable EDR/AV, or establish covert C2 tunnels.
- **Strict Grammar Rejection**: Offensive keywords and modification verbs (`execute`, `inject`, `load`, `disable`, `download`, `write`, `delete`, `kill`, `shell`) are explicitly rejected during parsing.

---

## 3. Supported Language Primitives

### 3.1 Statements

| Statement | Syntax | Purpose |
| :--- | :--- | :--- |
| `scan` | `scan <target> [where <condition>]` | Queries and filters active system state objects |
| `collect` | `collect <target> [, <target>]*` | Gathers forensic artifact categories |
| `hash` | `hash files in "<path>" [check against <service>]` | Computes file hashes within a specific directory |
| `check` | `check against <service>` | Triggers reputation/threat intelligence lookups |
| `flag` | `flag when <condition> [severity = <level>]` | Defines an in-memory alerting rule |
| `report` | `report to <destination>` | Specifies destination for collected evidence |

### 3.2 Targets
- `processes` — Running processes, signatures, parent-child lineages
- `connections` — Established and listening network sockets
- `files` — Filesystem metadata and file records
- `drivers` — Loaded kernel drivers and system modules
- `services` — System background services and startup types
- `autoruns` — Registry persistence keys and boot entries
- `scheduled_tasks` — Cron and Windows Task Scheduler entries
- `users` — Local and active user accounts
- `sessions` — Active logon sessions and terminal connections
- `event_logs` — System, Security, and Application event entries

### 3.3 Operators
- `==` / `eq` — Equality match
- `!=` / `neq` — Inequality match
- `>` / `gt` — Greater than
- `<` / `lt` — Less than
- `>=` / `gte` — Greater than or equal to
- `<=` / `lte` — Less than or equal to
- `contains` — Substring or array membership
- `in` — Element containment within an identifier or path

### 3.4 Severity Levels
- `low`
- `medium`
- `high`
- `critical`

### 3.5 Destinations
- `console`
- `server`

---

## 4. Formal Grammar (EBNF)

```ebnf
program         ::= statement+

statement       ::= scan_stmt
                  | collect_stmt
                  | hash_stmt
                  | check_stmt
                  | flag_stmt
                  | report_stmt

scan_stmt       ::= "scan" target ("where" condition)?
collect_stmt    ::= "collect" identifier ("," identifier)*
hash_stmt       ::= "hash" "files" "in" string ("check" "against" identifier)?
check_stmt      ::= "check" "against" identifier
flag_stmt       ::= "flag" "when" condition ("severity" "=" level)?
report_stmt     ::= "report" "to" destination

condition       ::= expression (("and" | "or") expression)*
expression      ::= identifier operator value

operator        ::= "==" | "!=" | ">" | "<" | ">=" | "<=" | "contains" | "in"
target          ::= "processes" | "connections" | "files" | "drivers" | "services"
                  | "autoruns" | "scheduled_tasks" | "users" | "sessions" | "event_logs"
level           ::= "low" | "medium" | "high" | "critical"
destination     ::= "console" | "server"
```

---

## 5. Concrete Script Example & Execution Plan

### 5.1 JOCKY Source Script
```jocky
# Forensic investigation query for suspicious unverified processes
scan processes
where signed == false
and network_connections > 0

collect autoruns, scheduled_tasks

hash files in "%TEMP%"
check against reputation

flag when signed == false
severity = high

report to server
```

### 5.2 Compiled JSON Execution Plan
```json
{
  "version": "1",
  "statements": [
    {
      "operation": "scan",
      "target": "processes",
      "where": {
        "operator": "and",
        "conditions": [
          {
            "field": "signed",
            "operator": "eq",
            "value": false
          },
          {
            "field": "network_connections",
            "operator": "gt",
            "value": 0
          }
        ]
      }
    },
    {
      "operation": "collect",
      "targets": [
        "autoruns",
        "scheduled_tasks"
      ]
    },
    {
      "operation": "hash",
      "target": "files",
      "path": "%TEMP%",
      "check_against": "reputation"
    },
    {
      "operation": "flag",
      "condition": {
        "field": "signed",
        "operator": "eq",
        "value": false
      },
      "severity": "high"
    },
    {
      "operation": "report",
      "destination": "server"
    }
  ]
}
```

---

## 6. Python Public API

The JOCKY language engine provides a standalone, clean Python interface decoupled from FastAPI:

```python
from app.jocky import (
    tokenize_jocky,
    parse_jocky,
    compile_jocky,
    compile_jocky_to_json,
    JockyError,
    JockyLexerError,
    JockyParserError,
    JockyValidationError,
)

source = """
scan processes where signed == false
report to console
"""

# 1. Compile directly to execution plan dict
plan = compile_jocky(source)
print(plan["version"])  # "1"

# 2. Compile directly to formatted JSON string
json_plan = compile_jocky_to_json(source, indent=2)

# 3. Access intermediate AST
ast = parse_jocky(source)
for statement in ast.statements:
    print(statement)
```

---

## 7. Error Handling & Diagnostics

JOCKY provides precise line and column diagnostics across all phases:

```
Lexer Error at line 3, column 12: Unexpected character '@'
Parser Error at line 2, column 18: Invalid severity level 'extreme' (expected: low | medium | high | critical)
Validation Error at line 1, column 1: Unsupported or disallowed offensive operation 'execute'. JOCKY is strictly a read-only forensic DSL.
```
