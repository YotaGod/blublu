# Test Scenario 4: Validation Engine & Drift Detection

This scenario tests the failure-detection capabilities of `scripts/validate-blueprint.py` and the self-healing routines of the `blublu validate` command.

---

## 1. Scenario Objective
Demonstrate that `scripts/validate-blueprint.py`:
1. Successfully detects broken file path references on disk.
2. Catches missing mandatory sections and unparseable Markdown tables.
3. Detects status tag corruptions and verification ratio inflation.
4. Returns correct nonzero exit codes (`1` for structural error, `2` for broken paths).

---

## 2. Failure Case Simulations

### Test Case A: Broken File References (`--check-files`)
1. In `tests/fixtures/simple-node-app/.agents/codebase-map.md`, introduce a non-existent path:
   ```markdown
   | `GhostService` | `src/services/ghostService.js` | Missing file | None | [Verified] |
   ```
2. Execute validation:
   ```bash
   python scripts/validate-blueprint.py --path tests/fixtures/simple-node-app/.agents/codebase-map.md --check-files
   ```
3. **Expected Result**:
   - Exit Code: `2`
   - Output contains: `Found 1 broken path reference(s) on disk: 'src/services/ghostService.js'`

---

### Test Case B: Corrupted Module Table Headers
1. Corrupt the Module Registry table header in `.agents/codebase-map.md`:
   ```markdown
   | Module | Path | Description | Status |
   ```
   *(Missing `Responsibility` and `Dependencies` columns)*
2. Execute validation:
   ```bash
   python scripts/validate-blueprint.py --path tests/fixtures/simple-node-app/.agents/codebase-map.md
   ```
3. **Expected Result**:
   - Exit Code: `1`
   - Output contains: `Module Registry missing expected column(s): responsibility, dependencies`

---

### Test Case C: Verification Ratio Drift
1. In Section 5, set 3 out of 4 modules to `[Stale]` or `[Unverified]`.
2. In Section 15, claim `Verification Ratio: 100%`.
3. Execute validation with `--strict`:
   ```bash
   python scripts/validate-blueprint.py --path tests/fixtures/simple-node-app/.agents/codebase-map.md --strict
   ```
4. **Expected Result**:
   - Exit Code: `1`
   - Output contains: `Section 15 declared ratio (100%) deviates from computed ratio (25%).`

---

## 3. Self-Healing Verification via Agent
When anomalies are detected:
1. Prompt agent:
   > *"blublu validate"*
2. Agent executes the repair checklist:
   - Removes `GhostService` or flags it as unmapped.
   - Re-inspects `src/services/` and confirms active modules.
   - Recalculates `Verification Ratio` and writes the correct percentage into Section 15.
3. Re-running `python scripts/validate-blueprint.py --check-files` returns Exit Code `0`.
