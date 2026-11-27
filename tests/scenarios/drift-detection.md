# Test Scenarios: Architecture Drift Detection (v2.0.0)

This document defines test scenarios for the `--check-drift` flag introduced in blublu v2.0.0.

**Command**: `python scripts/validate-blueprint.py --path <blueprint> --check-drift [--drift-exceptions <modules>]`
**CLI shortcut**: `python scripts/codsblu.py drift --path <dir>`

**Safety Guarantee**: ALL drift detection is READ-ONLY. Blueprint files are NEVER modified automatically.

---

## Scenario 1: Confirmed Drift — Structural Source File Change

**Setup**:
1. Start with `tests/fixtures/simple-node-app/.agents/codebase-map.md` (all modules `[Verified]`).
2. Modify `tests/fixtures/simple-node-app/src/services/userService.js` to add a new exported function:
   ```js
   exports.deleteUser = async (id) => { /* ... */ };
   ```
3. Do NOT update the blueprint.

**Command**:
```bash
python scripts/validate-blueprint.py \
  --path tests/fixtures/simple-node-app/.agents/codebase-map.md \
  --check-drift
```

**Expected Output**:
```
[!!] [Confirmed Drift] UserService
     Path: src/services
     Changed: src/services/userService.js
     Recommendation: Update blueprint for 'UserService' — structural/interface changes detected. Run: blublu update
```

**Pass Criteria**:
- `UserService` classified as `Confirmed Drift`.
- Exit code: 0 (non-strict mode; drift detected but no structural errors).
- Blueprint file `codebase-map.md` is UNCHANGED after the command.
- In `--strict` mode: exit code 2.

---

## Scenario 2: Potential Drift — Internal Implementation Change

**Setup**:
1. Modify `tests/fixtures/simple-node-app/src/services/userService.js` — change only an internal variable name (no new exports).
2. Do NOT update the blueprint.

**Command**:
```bash
python scripts/validate-blueprint.py \
  --path tests/fixtures/simple-node-app/.agents/codebase-map.md \
  --check-drift
```

**Expected Output**:
```
[??] [Potential Drift] UserService
     Path: src/services
     Changed: src/services/userService.js
     Recommendation: Review changes in 'UserService' — file changes detected but may be internal-only. Inspect and confirm.
```

**Pass Criteria**:
- `UserService` classified as `Potential Drift` (changed file, no structural keywords).
- No modules classified as `Confirmed Drift`.
- Exit code: 0.

---

## Scenario 3: Unverified Module

**Setup**: Use any fixture blueprint that contains a module with status `[Unverified]`.
(The `laravel-app` fixture contains modules with `[Inferred]` status.)

**Command**:
```bash
python scripts/validate-blueprint.py \
  --path tests/fixtures/laravel-app/.agents/codebase-map.md \
  --check-drift
```

**Expected Output** (for any [Inferred] or [Unverified] module):
```
[ ] [Unverified] <ModuleName>
     Path: <path>
     Recommendation: Inspect source at '<path>' and elevate status to [Verified].
```

**Pass Criteria**:
- Modules with `[Unverified]` or `[Stale]` status are classified as `Unverified` regardless of file changes.
- No false positives for `[Verified]` modules with no changed files.

---

## Scenario 4: User-Approved Exception

**Setup**: Use the simple-node-app fixture with a recently modified `userService.js`.

**Command** (mark UserService as a known exception):
```bash
python scripts/validate-blueprint.py \
  --path tests/fixtures/simple-node-app/.agents/codebase-map.md \
  --check-drift \
  --drift-exceptions "UserService,LegacyHelper"
```

**Expected Output**:
```
[ok] [User-Approved Exception] UserService
     Path: src/services
     Recommendation: No action required — explicitly approved by user.
```

**Pass Criteria**:
- `UserService` classified as `User-Approved Exception` (not Confirmed/Potential Drift).
- Other modules still correctly classified.
- Exit code: 0 (exception modules do not trigger strict-mode failure).

---

## Scenario 5: Non-Destructive Guarantee

**Purpose**: Verify that `--check-drift` NEVER modifies any blueprint file.

**Command**:
```bash
# Record hash before
python -c "import hashlib; d=open('tests/fixtures/simple-node-app/.agents/codebase-map.md','rb').read(); print(hashlib.sha256(d).hexdigest())"

# Run drift detection
python scripts/validate-blueprint.py \
  --path tests/fixtures/simple-node-app/.agents/codebase-map.md \
  --check-drift

# Record hash after
python -c "import hashlib; d=open('tests/fixtures/simple-node-app/.agents/codebase-map.md','rb').read(); print(hashlib.sha256(d).hexdigest())"
```

**Expected Result**: Both SHA256 hashes are identical.

**Pass Criteria**:
- Blueprint file hash is unchanged before and after `--check-drift`.
- No `.md` files in `.agents/` are created, modified, or deleted.
- Exit code: 0 (or 2 in strict mode if drift found, but file still unchanged).

---

## Scenario 6: JSON Format Output

**Command**:
```bash
python scripts/validate-blueprint.py \
  --path tests/fixtures/simple-node-app/.agents/codebase-map.md \
  --check-drift \
  --format json
```

**Expected JSON Structure** (embedded in validate output):
```json
{
  "valid": true,
  "drift": {
    "drift_report": [
      {
        "module": "UserService",
        "path": "src/services",
        "category": "Confirmed Drift",
        "changed_files": ["src/services/userService.js"],
        "recommendation": "Update blueprint for 'UserService'..."
      }
    ],
    "summary": {
      "confirmed": 1,
      "potential": 0,
      "unverified": 0,
      "approved_exceptions": 0
    }
  }
}
```

**Pass Criteria**:
- Output is valid JSON.
- `drift.drift_report` is a non-null array.
- `drift.summary` contains all 4 counters.
- Each report entry has: `module`, `path`, `category`, `changed_files`, `recommendation`.

---

## Scenario 7: Drift on Distributed (Enterprise Monorepo) Fixture

**Command**:
```bash
python scripts/validate-blueprint.py \
  --path tests/fixtures/enterprise-monorepo/.agents/codebase-map.md \
  --check-drift --strict
```

**Expected Behavior**:
- Validator reads Level 1 blueprint and identifies all 13 registered domains.
- For each domain, checks if source files under the domain's root path have changed.
- Reports drift per domain (not per file).
- Sub-blueprint content is also scanned if sub-blueprint files are registered.
- Exit code: 2 if any `Confirmed Drift` found in strict mode, 0 otherwise.

**Pass Criteria**:
- Drift report lists entries for domain-level modules (APIGateway, OrderService, etc.).
- No traceback or crash on distributed fixture.
- Non-destructive: `.agents/codebase-map.md` and all `.agents/sub-blueprints/*.md` unchanged.
