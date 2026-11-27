# Validation Rules & Audit Procedures

This reference defines how AI coding agents validate the accuracy of `.agents/codebase-map.md` against actual source files. Use these rules during the `validate` intent, during scheduled audits, or before major refactorings.

---

## 1. Validation Objectives

A codebase blueprint is only valuable if it is true. The validation process detects and repairs four common failure modes:

```
┌────────────────────────────────────────────────────────┐
│ 1. Broken File References                              │
│    Mapped files/paths that no longer exist on disk      │
├────────────────────────────────────────────────────────┤
│ 2. Orphaned / Unmapped Code                            │
│    Active source directories missing from the blueprint │
├────────────────────────────────────────────────────────┤
│ 3. Stale Data Flows & API Routes                       │
│    Flows referencing deprecated functions or endpoints  │
├────────────────────────────────────────────────────────┤
│ 4. Dependency Inconsistencies                          │
│    Claimed dependencies not present in code imports    │
└────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Validation Checklist

Execute this checklist sequentially when performing a `validate` task:

### Check 1: Existence of Registered Paths
- **Action**: Iterate over every file and directory path mentioned in:
  - Section 2: Entry Points
  - Section 5: Module Registry
  - Section 9: Database Mapping
  - Section 10: External Integrations
- **Verification**: Check if the path exists on disk.
- **Remediation**:
  - If a path no longer exists, search git log or file tree for renames.
  - If renamed/moved: Update the path in the blueprint.
  - If deleted: Remove the row or mark the component as removed.

### Check 2: Unmapped Directory Scan
- **Action**: Scan the immediate children of `src/`, `packages/`, `lib/`, or root source directories, excluding all patterns from [mapping-rules.md](file:///skills/blublu/references/mapping-rules.md).
- **Verification**: Compare discovered folders against the `Path` column in Section 5.
- **Remediation**:
  - If an active directory is not listed in Module Registry, inspect its index/entry file, determine its responsibility and dependencies, and append a new row with status `[Verified]`.

### Check 3: Public Export & Responsibility Verification
- **Action**: For each `[Verified]` module, inspect its primary entry file (e.g. `index.ts`, `mod.rs`, `__init__.py`).
- **Verification**: Do the exported functions, classes, or routers align with the stated responsibility?
- **Remediation**:
  - If responsibility has diverged, rewrite the responsibility text to match reality.
  - If the module was not inspected recently, demote status to `[Inferred]` or `[Stale]` until verified.

### Check 4: Dependency Graph Verification
- **Action**: Cross-examine Section 6 (Dependency Mapping) and the `Dependencies` column in Section 5.
- **Verification**:
  - Do module imports in code actually reflect the documented dependencies?
  - Are external packages declared in dependencies present in `package.json` / `Cargo.toml` / `pyproject.toml`?
- **Remediation**:
  - Add missing dependencies; prune dependencies that have been refactored away.
  - Update Mermaid graph arrows to reflect true import direction.

### Check 5: Data Flow & Endpoint Accuracy
- **Action**: For each data flow in Section 7 and route in Section 8:
  - Check that the referenced controller, service, or route handler exists.
  - Verify that the HTTP method and route path match route declarations in code.
- **Remediation**:
  - Correct route strings, HTTP verbs, or referenced function names.
  - Remove flows that describe deleted features.

---

## 3. Health Score & Status Metrics

Section 15 of `.agents/codebase-map.md` records the overall health of the architectural map. Compute and update these values during validation:

### Formulas & Thresholds

$$\text{Verification Ratio} = \left( \frac{\text{Count of [Verified] Modules}}{\text{Total Tracked Modules}} \right) \times 100\%$$

| Health Status | Verification Ratio | Criteria |
| :--- | :---: | :--- |
| **Healthy** | $\ge 90\%$ | All entry points exist, zero broken paths, $\ge 90\%$ modules `[Verified]`. |
| **Drift Detected** | $70\% - 89\%$ | $10\% - 30\%$ modules are `[Inferred]`, `[Unverified]`, or `[Stale]`, or 1–2 unmapped folders exist. |
| **Needs Rebuild** | $< 70\%$ | Core entry point broken, $> 30\%$ modules unverified/stale, or significant structural mismatch. |

---

## 4. Self-Healing & Audit Report Format

When the agent finishes a `validate` run, it should report findings in the following format:

```markdown
### blublu Blueprint Validation Report

- **Target File**: `.agents/codebase-map.md`
- **Result**: [PASSED | REPAIRED | REBUILD RECOMMENDED]
- **Verification Ratio**: XX% ([Verified] count / Total count)
- **Health Status**: [Healthy | Drift Detected | Needs Rebuild]

#### Discrepancies Found & Repaired:
1. **Broken Path**: `src/legacy-auth/` -> Path deleted; removed from Module Registry.
2. **Unmapped Module**: Found `src/modules/webhooks/` -> Added to Module Registry as `[Verified]`.
3. **Outdated Dependency**: `Auth` no longer depends on `Mailer` -> Pruned from Section 5 & 6.
4. **Stale Data Flow**: Flow #2 updated to reflect new queue name `email-tasks`.

*Blueprint synchronized and saved.*
```
