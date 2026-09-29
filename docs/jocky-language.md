# JOCKY Forensic Domain-Specific Language (DSL)

## 1. Vision & Purpose

**JOCKY** is a specialized, human-readable forensic interrogation language designed for incident responders and DFIR analysts. It allows analysts to write expressive queries that compile into deterministic JSON execution plans dispatched to fleet agents.

For the Hackathon MVP, JOCKY utilizes an **interpreted pipeline** (Lexer -> Parser -> AST -> Interpreter / Execution Planner). LLVM compilation is an explicit item on the post-MVP roadmap.

---

## 2. Language Grammar & Syntax Concept (Preview)

```jocky
// Sample JOCKY Forensic Script
TARGET os == "windows" AND tag == "workstation"

COLLECT processes
  WHERE name IN ["cmd.exe", "powershell.exe", "wscript.exe"]
  FILTER parent_name NOT IN ["explorer.exe", "services.exe"]
  WITH_HASH sha256

CHECK yara
  RULE "suspicious_obfuscated_powershell"
  ON process.command_line

COLLECT network_connections
  WHERE state == "ESTABLISHED" AND remote_port IN [4444, 1337, 8080]

ALERT IF detection.count > 0
  SEVERITY "HIGH"
  MESSAGE "Suspicious unsigned shell activity with non-standard parentage"
```

---

## 3. Pipeline Architecture

```
+---------------+      +---------------+      +---------------+
| JOCKY Script  | ---> | Lexer         | ---> | Parser        |
| Source (.jky) |      | (Token Stream)|      | (AST Builder) |
+---------------+      +---------------+      +---------------+
                                                     |
                                                     v
+---------------+      +---------------+      +---------------+
| Go Agent      | <--- | Execution     | <--- | AST Tree      |
| Execution Plan|      | Planner       |      | (Validation)  |
| (JSON Plan)   |      +---------------+      +---------------+
+---------------+
```

### Components:
- **Lexer** (`backend/app/jocky/lexer/`): Tokenizes keywords (`COLLECT`, `WHERE`, `TARGET`, `CHECK`, `ALERT`), identifiers, literals, and operators.
- **Parser** (`backend/app/jocky/parser/`): Builds recursive AST nodes ensuring syntax conformity and type checks.
- **AST** (`backend/app/jocky/ast/`): Represents statements (`TargetStatement`, `CollectStatement`, `CheckStatement`, `AlertStatement`).
- **Interpreter & Planner** (`backend/app/jocky/planner/`): Converts validated AST into optimized, portable JSON execution plans serialized for the Go Agent.

---

## 4. Execution Plan JSON Schema (Sample)

```json
{
  "plan_version": "1.0",
  "plan_id": "plan-90123",
  "targets": {
    "os": "windows"
  },
  "collectors": [
    {
      "type": "processes",
      "filters": {
        "names": ["cmd.exe", "powershell.exe"],
        "include_hashes": true
      }
    },
    {
      "type": "network",
      "filters": {
        "ports": [4444, 1337, 8080]
      }
    }
  ],
  "local_checks": [
    {
      "engine": "yara",
      "rule_id": "suspicious_obfuscated_powershell"
    }
  ]
}
```
