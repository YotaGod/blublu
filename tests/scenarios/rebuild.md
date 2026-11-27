# Test Scenario 3: Full Architecture Rebuild

This scenario simulates a significant architectural shift (e.g. migrating from an untyped monolith into modular feature slices) that necessitates wiping stale state and executing a complete rebuild.

---

## 1. Scenario Objective
Verify that the `rebuild` command:
1. Ignores previous cached assumptions in `.agents/codebase-map.md`.
2. Fully re-indexes the filesystem from scratch.
3. Completely purges deprecated modules, old data flows, and deleted file paths.
4. Resets the verification ratio and regenerates a fresh, verified blueprint.

---

## 2. Test Setup & Pre-conditions
- **Base Fixture**: `tests/fixtures/react-app`
- **Simulated Drift**:
  - Delete `src/components/Dashboard.jsx`.
  - Create `src/features/analytics/AnalyticsView.jsx`.
  - Move `src/hooks/useAuth.js` to `src/context/AuthContext.jsx`.

---

## 3. Execution Steps

### Step 3.1: Trigger Rebuild Intent
Prompt the agent:
> *"The project underwent a major directory reorganization. Run blublu rebuild."*

### Step 3.2: Agent Execution Protocol
1. Agent notes the `rebuild` intent.
2. Bypasses the incremental diff workflow.
3. Rescans `tests/fixtures/react-app/src/` completely.
4. Detects new directory `src/features/analytics/` and new context `src/context/AuthContext.jsx`.
5. Confirms that `src/components/Dashboard.jsx` and `src/hooks/useAuth.js` no longer exist on disk.
6. Rewrites all 15 sections of `.agents/codebase-map.md`.

---

## 4. Expected Assertions & Validation

### Assertion 1: Stale References Are Completely Purged
- Section 5 (Module Registry) must NOT contain `DashboardComponent` or `src/components/Dashboard.jsx`.
- Section 5 must contain `AnalyticsView` (`src/features/analytics/AnalyticsView.jsx`) and `AuthContext` (`src/context/AuthContext.jsx`).

### Assertion 2: Dependency Graph Consistency
- The Mermaid graph in Section 6 must reflect the new paths (`src/features/analytics/` and `src/context/AuthContext.jsx`).

### Assertion 3: Health Status Reset
- Section 15 must record:
  - `Health Status`: `Healthy`
  - `Verification Ratio`: `100%`
  - All tracked modules must be tagged `[Verified]`.

### Assertion 4: Automated Blueprint Validation
```bash
python scripts/validate-blueprint.py --path tests/fixtures/react-app/.agents/codebase-map.md --check-files
```
- **Exit Code**: `0`
- **Broken Paths Count**: `0`
