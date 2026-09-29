# JOCKY Forensic Agent (Go)

The **JOCKY Agent** is a cross-platform (Windows / Linux), read-only forensic collection and local detection agent written in Go.

---

## Architecture & Interfaces

- `cmd/agent/`: Application entry point (`main.go`).
- `internal/collectors/`: Pluggable forensic collector interfaces (`Collector`).
  - Planned: Processes, Network Sockets, Autoruns/Persistence, Scheduled Tasks, Services, Drivers/Modules, File Hashes, Event Logs, User Sessions.
- `internal/transport/`: Pluggable transport layer (`Transport`) for communicating with the management server.
- `internal/registration/`: Endpoint enrollment and identity exchange.
- `internal/detection/`: Local anomaly and rule-matching engine (e.g. YARA in-memory).
- `internal/runtime/`: Orchestrator executing compiled JSON plans received from the server.

---

## Build and Run

```bash
# Run locally from source
go run cmd/agent/main.go

# Build cross-platform binaries
# Windows (x64)
GOOS=windows GOARCH=amd64 go build -o bin/jocky-agent.exe cmd/agent/main.go

# Linux (x64)
GOOS=linux GOARCH=amd64 go build -o bin/jocky-agent cmd/agent/main.go

# Run tests
go test ./...
```
