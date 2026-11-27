# Update Rules: Synchronization & Lifecycle

This reference defines the protocols for keeping `.agents/codebase-map.md` updated as code evolves. It specifies incremental updating vs. full rebuilding, Git-aware inspection techniques, the change trigger matrix, and fallback procedures when Git is unavailable.

---

## 1. Incremental Update vs. Full Rebuild

Maintaining architectural memory requires efficiency. Agents must choose the correct update strategy:

```
                          ┌────────────────────────┐
                          │ Changes detected in PR │
                          │     or working copy    │
                          └───────────┬────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
    [Localized Changes]                             [Systemic Changes]
   • 1 to 5 modules touched                        • > 40% files moved/renamed
   • Internal route/schema update                  • Framework or runtime migration
   • Dependencies added/removed                    • Major directory restructuring
              │                                               │
              ▼                                               ▼
     INCREMENTAL UPDATE                                 FULL REBUILD
  - Update specific table rows                    - Re-scan entire repository
  - Refresh touched data flows                    - Regenerate all 15 sections
  - Update health ratio                           - Reset all statuses to verified
```

### Strategy Comparison

| Strategy | When to Use | Execution Speed | Scope |
| :--- | :--- | :--- | :--- |
| **Incremental Update** *(Default)* | After completing regular tasks, fixing bugs, adding endpoints, or updating schemas. | Fast (seconds) | Modifies only touched entries in Section 5 (Module Registry), Section 7 (Data Flows), Section 8/9/10, and updates Section 14 & 15. |
| **Full Rebuild** | Explicit `rebuild` command, major framework upgrades, monorepo reorganizations, or when validation detects severe drift. | Thorough (comprehensive) | Scans entire repository from scratch and rewrites `.agents/codebase-map.md`. |

---

## 2. Git-Aware Workflow

When Git is available, leverage Git's fast indexing to detect architectural changes instead of scanning the full disk tree.

### Step-by-Step Git Inspection

1. **Check Working Tree Status**:
   ```bash
   git status --short
   ```
   *Identifies untracked (`??`), added (`A`), modified (`M`), deleted (`D`), and renamed (`R`) files.*

2. **List Changed File Paths (Uncommitted or vs. Target Branch)**:
   ```bash
   git diff --name-only HEAD
   ```
   *or against base branch for feature branches:*
   ```bash
   git diff --name-only main...HEAD
   ```

3. **Inspect Scope and Scale of Changes**:
   ```bash
   git diff --stat HEAD
   ```
   *Provides lines added/deleted per file, revealing if a file was slightly edited or substantially overhauled.*

### Translating Git Changes to Blueprint Updates

- **Added files (`A` or `??`)**:
  - If placed inside an existing module, verify if module responsibility or exported contract expanded.
  - If a new directory was created under `src/` or `packages/`, add a new row to **Module Registry**.
  - If a new migration file was added, update **Database Mapping**.
- **Deleted files (`D`)**:
  - If an entire module directory was removed, delete its row from **Module Registry** and prune references in **Dependency Mapping** and **Data Flows**.
  - If an entry point was removed, update **Entry Points**.
- **Renamed or Moved files (`R`)**:
  - Update paths in **Entry Points**, **Directory Structure**, and **Module Registry**.
- **Modified files (`M`)**:
  - Evaluate against the **Change Trigger Matrix** below.

---

## 3. Change Trigger Matrix: Architectural vs. Non-Architectural

Not every file change justifies updating the blueprint. Agents must differentiate between **Architectural Changes** (requiring updates) and **Internal Logic Changes** (ignorable for blueprint purposes).

| Category | Example Changes | Blueprint Update Required? | Action Required in Blueprint |
| :--- | :--- | :---: | :--- |
| **New Module / Directory** | Created `src/modules/notifications/` | **YES** | Add row to Module Registry, update Directory Structure, update Mermaid graph. |
| **Deleted Module / File** | Removed legacy `src/utils/old-helper.ts` | **YES** | Remove from Module Registry, prune stale dependencies. |
| **Module Contract / API Change** | Added new exported function/class, altered method signature | **YES** | Update Module Responsibility column, update affected Data Flow. |
| **Route / Endpoint Change** | Added `POST /api/v2/payments`, removed deprecated route | **YES** | Update Section 8 (API Mapping). |
| **Database Schema Change** | Added new table, altered column types, created migration | **YES** | Update Section 9 (Database Mapping). |
| **External Integration Change** | Added Stripe webhook handler, changed email provider | **YES** | Update Section 10 (External Integrations). |
| **Dependency Manifest Change** | Added `pino` or `drizzle-orm` in `package.json` | **YES** | Update Section 1 Tech Stack or Section 6 Dependencies. |
| **Configuration Change** | Added new required environment variable in config | **YES** | Update Section 10 or Section 11 Project Conventions. |
| **Internal Bug Fix** | Corrected off-by-one error or null check inside existing function | **NO** | No architectural impact. Do not update blueprint. |
| **Refactoring within Module** | Renamed local variable, extracted private helper function | **NO** | No external contract change. Do not update blueprint. |
| **Unit Test Addition** | Added `src/modules/auth/service.test.ts` | **NO** | Test files are tracked as conventions, not independent modules. |
| **Styling / Markup Tweaks** | Changed Tailwind CSS utility classes, updated copy | **NO** | Presentation details. Do not update blueprint. |
| **Dependency Patch Bump** | Bumped minor patch version in lockfile (e.g., 1.2.3 -> 1.2.4) | **NO** | No structural impact. Do not update blueprint. |

---

## 4. Post-Coding Blueprint Update Protocol

When concluding any task that introduced an architectural change:

1. **Identify Affected Sections**:
   Determine which of the 15 sections are impacted (e.g., Module Registry + API Mapping + Recent Changes).
2. **Perform Surgical Updates**:
   Use precision edits to update only the affected rows or bullet points. Avoid regenerating untouched text.
3. **Log to Recent Architectural Changes (Section 14)**:
   Add a one-line entry with the current date (YYYY-MM-DD) and a concise summary of the architectural change. Keep the section trimmed to the last 5–10 items.
4. **Update Mapping Health (Section 15)**:
   - Update `Last Updated` to current UTC timestamp.
   - Update `Agent / Tool` identifier.
   - Re-compute `Verification Ratio` if statuses changed.

---

## 5. Non-Git Fallback Protocol

If the codebase is not tracked by Git, or if the `git` CLI is unavailable:

1. **Filesystem Inspection**:
   - Run recursive file listing commands on the source directory (e.g. `Get-ChildItem -Recurse -File` on PowerShell or `find . -type f` on POSIX).
   - Filter through the Ignore Patterns in [mapping-rules.md](file:///skills/blublu/references/mapping-rules.md).
2. **Compare Against Existing Registry**:
   - Compare discovered file paths against the `Path` column in Section 5 (Module Registry).
   - Detect new directories that are unmapped.
   - Detect mapped paths that no longer exist on disk.
3. **Inspect File Modification Timestamps**:
   - Look for files whose last-modified timestamp is newer than the `Last Updated` timestamp in Section 15.
   - Analyze those modified files for architectural changes.
