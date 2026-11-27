# Test Scenario: Distributed Blueprint Architecture & Progressive Loading

This scenario evaluates the **Codsblu v1.2.0 Distributed Architecture** capabilities, testing:
1. Multi-domain index parsing via `Sub-Blueprints Index`.
2. Validation of all registered sub-blueprints.
3. Detection of orphaned sub-blueprints.
4. Compliance with Context-Aware / Progressive Loading rules.

---

## 1. Test Setup
- **Target Fixture**: `tests/fixtures/distributed-app`
- **Structure**:
  - Root Index: `tests/fixtures/distributed-app/.agents/codebase-map.md`
  - Sub-Blueprints:
    - `.agents/sub-blueprints/api.md`
    - `.agents/sub-blueprints/web.md`

---

## 2. Validation Execution

Run the validator against the distributed fixture:
```bash
python scripts/validate-blueprint.py --path tests/fixtures/distributed-app/.agents/codebase-map.md --strict --check-files
```

### Expected Output & Assertions:
1. **Mode Detected**: `Distributed (2 sub-blueprints)`.
2. **Sub-Blueprints**: 2 registered, 0 missing, 0 orphaned.
3. **Exit Code**: `0` (PASS).

---

## 3. Orphaned Sub-Blueprint Test

1. Create an untracked sub-blueprint on disk:
   ```bash
   echo "# Domain Blueprint: Rogue" > tests/fixtures/distributed-app/.agents/sub-blueprints/rogue.md
   ```
2. Re-run validator with `--strict`:
   ```bash
   python scripts/validate-blueprint.py --path tests/fixtures/distributed-app/.agents/codebase-map.md --strict
   ```
3. **Expected Assertions**:
   - Error or warning: `Orphaned sub-blueprint '.agents/sub-blueprints/rogue.md' exists on disk but is not indexed in root blueprint.`
   - In `--strict` mode, exit code is non-zero (`1`).
4. Clean up `rogue.md`:
   ```bash
   rm -f tests/fixtures/distributed-app/.agents/sub-blueprints/rogue.md
   ```

---

## 4. Context-Aware Progressive Loading Rule

When an AI coding agent is tasked:
> *"Update the API server port in apps/api/server.js"*

- **Protocol**:
  1. Agent reads `.agents/codebase-map.md`.
  2. Resolves that `apps/api` belongs to the `API` domain.
  3. Loads ONLY `.agents/sub-blueprints/api.md` into context.
  4. Agent DOES NOT read `.agents/sub-blueprints/web.md`, preserving ~1,500 tokens.
