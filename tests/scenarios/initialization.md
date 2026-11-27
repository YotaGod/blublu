# Test Scenario 1: Fresh Codebase Initialization

This scenario guides the end-to-end evaluation of the `initialize` intent on a newly onboarded project lacking an existing architectural blueprint.

---

## 1. Scenario Objective
Verify that an AI coding agent executing `blublu initialize`:
1. Recursively discovers project files while observing all ignore rules.
2. Accurately determines technology stack, runtime, and primary entry point.
3. Generates `.agents/codebase-map.md` conforming to the 15-section template.
4. Keeps initial token footprint under 1,500 words / 2,000 tokens.

---

## 2. Test Setup & Pre-conditions
- **Target Repository**: `tests/fixtures/simple-node-app`
- **Starting State**: Ensure no `.agents/codebase-map.md` exists prior to test:
  ```bash
  rm -f tests/fixtures/simple-node-app/.agents/codebase-map.md
  ```

---

## 3. Execution Steps

### Step 3.1: Trigger Initialization Prompt
Send the following prompt to the AI agent:
> *"Initialize blublu on this repository and create the architectural blueprint."*

### Step 3.2: Agent Execution Protocol
The agent should execute the following operations:
1. Scan root manifests: identifies `package.json` (`express`, `cors`, `dotenv`).
2. Identify entry point: inspects `main` property in `package.json` (`src/index.js`).
3. Traverse `src/` directory:
   - Identifies `src/routes/users.js` as routing layer.
   - Identifies `src/controllers/userController.js` as presentation/controller layer.
   - Identifies `src/services/userService.js` as business domain layer.
4. Creates `.agents/codebase-map.md` using `blueprint-template.md`.
5. Sets module status tags: assigns `[Verified]` or `[Inferred]`.
6. Marks irrelevant sections (e.g. Database / External Integrations) as `N/A`.

---

## 4. Expected Assertions & Validation

### Assertion 1: Blueprint Exists and Contains 15 Sections
Verify using the Python validator:
```bash
python scripts/validate-blueprint.py --path tests/fixtures/simple-node-app/.agents/codebase-map.md --check-files
```
- **Expected Exit Code**: `0` (Success).
- **Expected Health**: `Healthy` (Verification Ratio $\ge 90\%$).

### Assertion 2: Entry Points and Module Registry Accuracy
- `src/index.js` must be listed under Section 2 (Entry Points).
- Exactly 4 modules must be tracked in Section 5 (Module Registry).
- No temporary files, `.DS_Store`, or `node_modules` should appear in any section.

### Assertion 3: Token Efficiency Check
- Total line count of `.agents/codebase-map.md` should be between 80 and 150 lines.
- File size should be under 8 KB.
