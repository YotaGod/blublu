# Test Scenario: Codsblu CLI & Local Filesystem Watcher

This scenario verifies the CLI commands and the local background file watcher implemented in **Codsblu v1.2.0**.

---

## 1. CLI Commands Verification

### A. Status Command
```bash
python scripts/codsblu.py status --path tests/fixtures/distributed-app
```
**Expected Output**:
- Displays `Architecture Mode: Distributed (2 sub-blueprints)`.
- Displays `Tracked Modules: 2`.
- Displays `Verification Ratio: 100% (Healthy)`.
- Reports background watcher status.

### B. Validation via CLI
```bash
python scripts/codsblu.py validate --path tests/fixtures/distributed-app --strict --check-files
```
**Expected Output**:
- Runs validation and exits with code `0`.

### C. Migration to Distributed
Test migration on a copy of a single-file fixture:
```bash
python scripts/codsblu.py migrate --to-distributed --path tests/fixtures/simple-node-app
```
**Expected Output**:
- Sub-blueprints created inside `.agents/sub-blueprints/`.
- Root blueprint updated with `Sub-Blueprints Index`.

---

## 2. Background Filesystem Watcher Verification

### A. Start Watcher
```bash
python scripts/codsblu.py watch --path tests/fixtures/simple-node-app --debounce 1000 &
```
- Creates PID file: `tests/fixtures/simple-node-app/.agents/.codsblu.pid`.

### B. Verify Status
```bash
python scripts/codsblu.py status --path tests/fixtures/simple-node-app
```
- Reports `Background Watcher: RUNNING (PID: ...)`.

### C. Trigger File Change
```bash
echo "// new route" >> tests/fixtures/simple-node-app/src/routes/users.js
sleep 1.5
```
- Watcher batches change and writes to `tests/fixtures/simple-node-app/.agents/.pending-changes.json`.
- Event queue records `src/routes/users.js`.

### D. Stop Watcher
```bash
python scripts/codsblu.py stop --path tests/fixtures/simple-node-app
```
- Process terminated, PID file removed.
- Status returns `Background Watcher: STOPPED`.
