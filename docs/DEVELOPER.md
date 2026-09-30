# JOCKY Developer Documentation & Implementation Truth

## Implementation Status Table

| Component | Status |
|-----------|--------|
| JOCKY DSL | IMPLEMENTED |
| Agent runtime | IMPLEMENTED |
| Process collector | IMPLEMENTED |
| Network collector | IMPLEMENTED |
| Autorun collector | IMPLEMENTED |
| Scheduled task collector | IMPLEMENTED |
| User collector | IMPLEMENTED |
| Session collector | IMPLEMENTED |
| File collector | PLACEHOLDER |
| Driver collector | PLACEHOLDER |
| Service collector | PLACEHOLDER |
| Event log collector | PLACEHOLDER |
| Agent transport | IMPLEMENTED |
| Detection engine | IMPLEMENTED |
| Dashboard | NOT STARTED |

---

## 1. Last Completed Task
**Phase 6 — Persistence & Identity Collectors**

---

## 2. Last Verified State

- **Go Agent Test Suite & Build**:
  - `go test -v -count=1 ./...` -> **31/31 tests PASSED** across `internal/collectors`, `internal/runtime`, and `tests`.
  - `go build ./...` -> **Binary build SUCCESSFUL** (exit code 0).
- **Python Backend Test Suite**:
  - `python -m pytest -v` -> **58/58 tests PASSED** in 1.55s across detection, persistence, collectors, DSL, AST, and API routes.

---

## 3. Current Working Functionality

The Go forensic agent can now collect read-only telemetry across six core targets:
1. **`processes`**: Read-only process enumeration (`PID`, `PPID`, `Name`, `Path`, `CommandLine`, `User`, `SignatureStatus`).
2. **`connections`**: Read-only socket/network state (`Protocol`, `LocalAddress`, `LocalPort`, `RemoteAddress`, `RemotePort`, `State`, `PID`).
3. **`autoruns`**: Read-only persistence enumeration (`Location`, `Name`, `Command`, `User`, `Source`, `Enabled`).
4. **`scheduled_tasks`**: Read-only task and cron inspection (`Name`, `Path`, `Author`, `Action`, `Arguments`, `Trigger`, `Enabled`, `User`).
5. **`users`**: Read-only local user account enumeration (`Username`, `SID`, `UID`, `GID`, `HomeDir`, `Shell`, `Enabled`, `AccountType`, `Description`). No credential extraction or password hashes accessed.
6. **`sessions`**: Read-only active session inspection (`Username`, `SessionID`, `SessionName`, `Terminal`, `State`, `LogonType`, `ClientName`, `Source`, `LoginTime`). No credential access.

Execution plans compiled from JOCKY DSL trigger only the requested collectors, validate plans before execution, and transmit normalized artifacts to FastAPI via HTTP transport.

---

## 4. Phase 6 — Persistence & Identity Collectors

### 4.1 Autorun Collector (`AutorunCollector`)
- **Target**: `autoruns`
- **Artifact Type**: `autorun`
- **Windows Implementation (`autoruns_windows.go`)**:
  - Reads registry Run and RunOnce keys via read-only queries (`HKLM\...\Run`, `HKLM\...\RunOnce`, `HKCU\...\Run`, `HKCU\...\RunOnce`, Wow6432Node).
  - Inspects user and system startup directories (`%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup` and `%APPDATA%\...`).
- **Linux Implementation (`autoruns_linux.go`)**:
  - Enumerates `.desktop` files in `/etc/xdg/autostart/` and `~/.config/autostart/`.
  - Inspects system startup scripts (`/etc/rc.local`).
- **Safety**: Purely read-only; does not create, modify, or execute persistence entries.

### 4.2 Scheduled Task Collector (`ScheduledTaskCollector`)
- **Target**: `scheduled_tasks`
- **Artifact Type**: `scheduled_task`
- **Windows Implementation (`scheduled_tasks_windows.go`)**:
  - Queries scheduled tasks via `schtasks /query /fo CSV /v`.
  - Captures task name, path, author, action command, arguments, trigger schedule, and enabled state.
- **Linux Implementation (`scheduled_tasks_linux.go`)**:
  - Reads `/etc/crontab`, system cron directories (`/etc/cron.d/`), and user crontabs (`/var/spool/cron/crontabs/`).
  - Normalizes cron schedule intervals (`m h dom mon dow`) and target execution commands.
- **Platform Differences**:
  - Windows scheduled tasks are XML/COM-defined objects supporting calendar, system event, logon, and boot triggers with principal user contexts.
  - Linux cron entries are time-interval expression strings executing shell commands under configured user IDs.

### 4.3 User Collector (`UserCollector`)
- **Target**: `users`
- **Artifact Type**: `user`
- **Windows Implementation (`users_windows.go`)**:
  - Enumerates local user accounts via read-only `net user` queries.
  - Identifies built-in administrator, guest, and local user accounts.
- **Linux Implementation (`users_linux.go`)**:
  - Reads `/etc/passwd`.
  - Extracts username, UID, GID, home directory, shell, and determines enabled status based on shell interactiveness (`/usr/sbin/nologin` or `/bin/false` -> disabled).
- **Safety**: Never accesses credential stores, SAM database, or shadow files. Never attempts authentication.

### 4.4 Session Collector (`SessionCollector`)
- **Target**: `sessions`
- **Artifact Type**: `session`
- **Windows Implementation (`sessions_windows.go`)**:
  - Queries active user sessions via `query session` / `qwinsta`.
  - Extracts session ID, session name, username, state (`Active`, `Disc`), and logon type (`Console`, `RDP`, `Service`).
- **Linux Implementation (`sessions_linux.go`)**:
  - Queries login sessions via standard `who` interface.
  - Extracts username, terminal device (`tty1`, `pts/0`), source IP/host, and login timestamp.

### 4.5 Registry Integration
- Real collectors registered for: `processes`, `connections`, `autoruns`, `scheduled_tasks`, `users`, `sessions`.
- Placeholder collectors retained for: `files`, `drivers`, `services`, `event_logs`.
- Verified thread-safe registry in `agent/internal/collectors/registry.go`.

---

## 5. Current Contracts

### Artifact Schemas

#### Autorun Artifact
```json
{
  "type": "autorun",
  "collected_at": "2026-09-30T10:00:00Z",
  "data": {
    "name": "SecurityHealth",
    "location": "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
    "command": "C:\\Windows\\System32\\SecurityHealthSystray.exe",
    "user": "SYSTEM",
    "source": "registry",
    "enabled": true
  }
}
```

#### Scheduled Task Artifact
```json
{
  "type": "scheduled_task",
  "collected_at": "2026-09-30T10:00:00Z",
  "data": {
    "name": "\\Microsoft\\Windows\\UpdateOrchestrator\\Schedule Scan",
    "path": "\\Microsoft\\Windows\\UpdateOrchestrator\\Schedule Scan",
    "author": "Microsoft Corporation",
    "action": "C:\\Windows\\system32\\usoclient.exe StartScan",
    "arguments": "StartScan",
    "trigger": "Daily",
    "enabled": true,
    "user": "NT AUTHORITY\\SYSTEM"
  }
}
```

#### User Artifact
```json
{
  "type": "user",
  "collected_at": "2026-09-30T10:00:00Z",
  "data": {
    "username": "sysadmin",
    "sid": "S-1-5-21-...",
    "uid": 1001,
    "gid": 1001,
    "home_dir": "/home/sysadmin",
    "shell": "/bin/bash",
    "enabled": true,
    "account_type": "local",
    "description": "System Administrator"
  }
}
```

#### Session Artifact
```json
{
  "type": "session",
  "collected_at": "2026-09-30T10:00:00Z",
  "data": {
    "username": "Alice",
    "session_id": "1",
    "session_name": "console",
    "terminal": "console",
    "state": "Active",
    "logon_type": "Console",
    "client_name": "local",
    "source": "local",
    "login_time": "2026-09-30 08:30"
  }
}
```

### Detection Rules Added
- `AUTORUN-SUSP-001`: Detects autorun persistence entries configured to execute binaries from temporary or volatile user directories (`\temp\`, `/tmp/`).
- `USER-SUSP-001`: Detects dormant, guest, or suspicious backdoor accounts active in an enabled state.

---

## 6. Current Limitations

1. **Placeholder Collectors**: The remaining four collectors (`files`, `drivers`, `services`, `event_logs`) remain safe placeholders.
2. **YARA & Sigma Engines**: Binary scanning and Sigma rule engines are not yet integrated into the runtime.
3. **Frontend Dashboard**: The React web interface has not yet been hooked up to live agent endpoints and WebSocket streams.

---

## 7. Exactly ONE Next Recommended Step

**Phase 7: Frontend React Dashboard & Live Forensic Triage Interface**
- Connect React dashboard to FastAPI management endpoints (`/api/v1/agents`, `/api/v1/jobs`, `/api/v1/artifacts`, `/api/v1/detections`).
- Build real-time forensic triage table subscribing to WebSocket `/ws/jobs/{job_id}`.
- Provide interactive JOCKY DSL script dispatch, live artifact stream, and evidence drill-down inspector.

---

## 8. Prior Completed Phases

### Phase 1 — JOCKY Language MVP
- Implemented lexer, parser, AST nodes, execution planner, and validation.
- Verbs: `scan`, `collect`, `hash`, `check`, `flag`, `report`.

### Phase 2 — Go Agent Execution Foundation
- Implemented execution runtime, typed execution plans, collector interface, and placeholder registry.

### Phase 3 — Process + Network Collectors
- Implemented read-only collectors for `processes` and `connections` with Windows/Linux platform separation.

### Phase 4 — Agent ↔ Server Transport
- Implemented agent registration, heartbeat loop, job polling, artifact submission, and bearer authentication boundary.

### Phase 5 — Detection & Correlation Engine
- Implemented explainable detection engine, persistence, deduplication, JOCKY `flag` dynamic condition evaluation, and `GET /api/v1/detections` API.
