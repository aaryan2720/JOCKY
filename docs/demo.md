# JOCKY Hackathon Demo Script & Walkthrough

## 1. Hackathon Demo Narrative

1. **The Scenario**:
   - A potential insider threat or lateral movement anomaly is detected across the fleet.
   - An incident responder opens the JOCKY React Dashboard.

2. **Fleet Inspection**:
   - Analyst navigates to `/fleet` to verify live agent heartbeats and connected Windows / Linux nodes.

3. **DSL Script Composition**:
   - Analyst opens `/editor` and writes a fast JOCKY query targeting suspicious process lineages and persistence keys.
   - The query syntax is validated in real time against the backend AST engine.

4. **Live Job Dispatch**:
   - Analyst executes the script across all Windows endpoints.
   - Dispatcher compiles the AST to a JSON plan and pushes it via WebSocket / mTLS to the Go Agents.

5. **Live Evidence & Threat Correlation**:
   - Analyst watches `/results` populate live with collected artifacts (process hashes, network sockets, autoruns).
   - Local and backend detection engines flag matching Sigma/YARA rules with high-confidence explanations on `/threats`.

---

## 2. Verification Checklist for Presenters

- [ ] Backend is running on port 8000 and `/health` returns status `ok`.
- [ ] Frontend is reachable on port 5173 with smooth navigation across Fleet, Editor, Deployments, Results, and Threats.
- [ ] Go agent starts without errors and logs initialization message.
- [ ] Postgres / Redis containers are operational via Docker Compose.
