# User & Developer Guide: Working with blublu

This guide outlines practical daily workflows, manual command usage, best practices for preventing blueprint bloat, and troubleshooting techniques.

---

## 1. Daily Workflow: The Automatic Lifecycle

When blublu is active, you do not need to constantly tell the agent to manage documentation. The agent automatically executes the **Three-Phase Lifecycle** during regular coding tasks:

```
┌────────────────────────────────────────────────────────┐
│ Phase 1: BEFORE TASK                                   │
│ • Reads `.agents/codebase-map.md`                      │
│ • Loads module boundaries & project conventions        │
├────────────────────────────────────────────────────────┤
│ Phase 2: DURING TASK                                   │
│ • Implements feature/fix adhering to architectural rules│
│ • Flags created/deleted/renamed files                  │
├────────────────────────────────────────────────────────┤
│ Phase 3: AFTER TASK                                    │
│ • Runs `git diff` to assess architectural impact       │
│ • If architectural: surgically updates blueprint       │
└────────────────────────────────────────────────────────┘
```

### Example User Experience:
- **You ask**: *"Add a rate-limiter middleware to the checkout route."*
- **Agent reads**: `.agents/codebase-map.md` (identifies that `Billing` module handles checkout and `Redis` is used for caching).
- **Agent codes**: Implements rate limiting in `src/modules/billing/middleware.ts`.
- **Agent updates**: Updates the `Billing` entry in Section 5, records the new dependency in Section 6, logs a one-line entry in Section 14, and updates the timestamp in Section 15.

---

## 2. Explicit Commands & Natural Prompts

When you want direct control over the blueprint, you can trigger specific intents using natural conversational prompts:

### `initialize`
- **When to use**: Onboarding an existing codebase or bootstrapping a new project.
- **Example Prompts**:
  - *"Initialize blublu on this repository."*
  - *"Generate the initial .agents/codebase-map.md blueprint."*
- **What happens**: The agent scans directory trees, identifies frameworks and entry points, and populates all 15 sections according to the template.

### `update`
- **When to use**: After finishing manual git changes or pulling commits from teammates.
- **Example Prompts**:
  - *"blublu update"*
  - *"Sync the codebase map with my recent git changes."*
- **What happens**: The agent inspects `git status` and `git diff`, updating only the modified rows, schemas, or routes.

### `rebuild`
- **When to use**: After major framework migrations or extensive directory restructuring.
- **Example Prompts**:
  - *"blublu rebuild"*
  - *"Re-scan the full project and regenerate the blueprint from scratch."*
- **What happens**: The agent re-analyzes every source module, resets statuses to `[Verified]`, and rewrites the complete map.

### `validate`
- **When to use**: Periodic quality check or pre-merge validation.
- **Example Prompts**:
  - *"blublu validate"*
  - *"Check if our codebase map has any broken file paths or stale modules."*
- **What happens**: The agent verifies every path against the filesystem, flags orphaned directories, repairs discrepancies, and outputs a validation report with the Verification Ratio.

### `impact [module]`
- **When to use**: Before refactoring a critical component or deleting legacy code.
- **Example Prompts**:
  - *"blublu impact src/modules/auth"*
  - *"What is the blast radius if I modify the User module?"*
- **What happens**: The agent inspects the `Module Registry`, `Dependency Mapping`, and `Main Data Flows`, listing all downstream modules, routes, and external services that could break.

### `status`
- **When to use**: Quick health check of the architectural memory.
- **Example Prompts**:
  - *"blublu status"*
  - *"Show me the current codebase map health."*
- **What happens**: The agent reports the last updated date, total tracked modules, verification percentage, and current health rating (`Healthy`, `Drift Detected`, or `Needs Rebuild`).

---

## 3. Best Practices: Keeping the Blueprint Compact (Anti-Bloat)

To ensure the blueprint remains fast to read and token-efficient across hundreds of agent sessions, follow these rules:

1. **Keep Explanations Dense**:
   - Write module responsibilities in 1–2 factual sentences describing capabilities, not internal mechanics.
   - Example: `"Processes Stripe webhook callbacks and records invoice ledger entries."` (Good) vs. 4 paragraphs detailing every switch-case statement (Bad).
2. **Never Paste Raw Code Snippets**:
   - Link to file paths instead of copying raw functions or class definitions into the markdown.
3. **Limit Directory Tree Depth**:
   - Keep Section 3 (Directory Structure) limited to 2–3 levels. Do not list every file in every subdirectory.
4. **Prune Stale Architectural Changes**:
   - Keep Section 14 (Recent Architectural Changes) capped at the 5 to 10 most recent entries. Remove older entries.
5. **Mark Irrelevant Sections N/A**:
   - If your project has no database, write `*N/A — Stateless application*` under Section 9 rather than leaving speculative placeholders.

---

## 4. Troubleshooting & FAQ

### Issue: The agent claims a file exists in the blueprint, but it was moved or deleted.
- **Cause**: The file was modified outside of an agent session without running an update.
- **Fix**: Run prompt: *"blublu validate"*. The agent will scan the filesystem, detect the missing file, locate the new path, and repair the blueprint.

### Issue: Git merge conflict in `.agents/codebase-map.md`.
- **Cause**: Two branches updated the blueprint concurrently.
- **Fix**: Accept either version (or combine rows in Section 5), then instruct the agent: *"blublu update"*. The agent will resolve the table rows against the current working tree.

### Issue: The blueprint is growing too large (> 3,000 tokens).
- **Cause**: Too many detailed subroutines or data flows recorded.
- **Fix**: Prompt: *"blublu rebuild with Level 2 balanced depth focus"*. The agent will consolidate micro-details into concise module responsibilities.

---

## 5. v1.1.0 Intelligence & CI/CD Tooling

Version 1.1.0 introduces automated change detection, diagram validation, and CI gatekeeping tools:

### A. Advanced Filesystem Scanner (`scripts/scanner.py`)
Run the scanner directly to inspect what files have changed in your working tree:
```bash
# Scan current repository (automatically selects Git or Filesystem fallback)
python scripts/scanner.py

# Scan a non-git directory and emit JSON
python scripts/scanner.py --path /path/to/project --format json
```
- In Git repositories: uses `git status --short` and `git diff --name-only`.
- In non-Git repositories: traverses filesystem safely (`follow_symlinks=False`), ignoring build artifacts, and caches metadata in `.agents/.cache_scan.json`.

### B. Staleness & Architecture Drift Detection
Ensure your blueprint hasn't fallen behind recent code commits:
```bash
python scripts/validate-blueprint.py --check-staleness
```
- If source files in a module's directory were modified on disk without an update to `.agents/codebase-map.md`, the validator flags the module as stale.
- Add `--strict` to treat staleness as an exit-code failure in automated pipelines.

### C. Automated Mermaid Diagram Validation & Fallback
The validator automatically verifies all Mermaid blocks in Section 6:
```bash
python scripts/validate-blueprint.py
```
- Checks bracket balancing (`[]`, `()`, `{}`).
- Validates arrow syntax (`-->`, `-.->`, `==>`).
- If a diagram is invalid, the validator automatically prints a **Fallback Relationship Table** recommendation in Markdown so you can replace the broken diagram immediately.

### D. GitHub Actions CI Integration
Codsblu ships with two official GitHub Actions workflows in `.github/workflows/`:
1. `blublu-validate.yml`: Runs on push and PR to ensure blueprint syntax, table structure, and referenced files are valid.
2. `blublu-architecture-check.yml`: Analyzes PR file deltas and posts a warning annotation if code files were changed without synchronizing `.agents/codebase-map.md`.

---

## 6. v1.2.0 Distributed Architecture & Automation Tooling

Version 1.2.0 introduces the unified `blublu` CLI, multi-file (distributed) blueprint support, and a background filesystem watcher.

### A. Unified CLI: `blublu`

The `blublu` command is the primary interface for all blublu operations from your terminal. Cross-platform launchers are included:

| Platform | Launcher |
|---|---|
| Linux / macOS | `scripts/blublu` (POSIX shell wrapper) |
| Windows PowerShell | `scripts/blublu.ps1` |
| Windows CMD | `scripts/blublu.cmd` |
| Direct Python | `python scripts/blublu.py <command>` |

#### Commands

```bash
# Initialize blueprint (single-file mode, default)
blublu init [--path <project-dir>]

# Initialize with distributed sub-blueprint support
blublu init --distributed [--path <project-dir>]

# Show current blueprint health, mode, and stats
blublu status [--path <project-dir>] [--format json]

# Validate blueprint structure, paths, and sub-blueprints
blublu validate [--path <project-dir>] [--check-files] [--check-staleness] [--strict] [--format json]

# Migrate a single-file blueprint to distributed mode
blublu migrate --to-distributed [--path <project-dir>]

# Start the background filesystem watcher (debounced change detection)
blublu watch [--path <project-dir>] [--debounce <ms>] [--interval <seconds>]

# Stop the background watcher
blublu stop [--path <project-dir>]
```

#### Global Options

| Flag | Default | Description |
|---|---|---|
| `--path <dir>` | `.` (current dir) | Root directory of the project to operate on |
| `--format text\|json` | `text` | Output format for `status` and `validate` |
| `--strict` | off | Exit code 1 on warnings (staleness, orphaned sub-blueprints) |
| `--check-files` | off | Verify that all referenced paths exist on disk |
| `--check-staleness` | off | Flag modules whose source files are newer than the blueprint |

---

### B. Distributed Blueprint Mode

For projects with many independent domains, v1.2.0 supports a **distributed** architecture where the root `.agents/codebase-map.md` acts as an index pointing to per-domain sub-blueprints stored in `.agents/sub-blueprints/`.

#### Directory Layout (Distributed)

```
.agents/
├── codebase-map.md              ← Root index (always loaded first)
└── sub-blueprints/
    ├── api.md                   ← Domain: API service
    ├── web.md                   ← Domain: Web frontend
    └── auth.md                  ← Domain: Auth service
```

#### Progressive Loading Rule (Mandatory)
Agents **must not** load all sub-blueprints at once. The correct loading procedure is:

1. **Always read `codebase-map.md` first** — this contains the Sub-Blueprints Index (Section 5).
2. **Identify which domain(s) are touched** by the current user prompt.
3. **Load only the matching sub-blueprint(s)** — ignore all others.

```
User prompt: "Add rate limiting to the API checkout route"
                        │
                        ▼
         Load: .agents/codebase-map.md (index)
                        │
                        ▼
         Identify: "API" domain is touched
                        │
                        ▼
         Load: .agents/sub-blueprints/api.md ONLY
         Skip: web.md, auth.md (not relevant)
```

#### Migrating to Distributed Mode

```bash
# Migrate an existing single-file project
blublu migrate --to-distributed --path /your/project

# Verify the migration result
blublu validate --path /your/project --check-files --strict
```

---

### C. Background Filesystem Watcher (`blublu watch`)

The watcher monitors your project directory continuously and writes pending change events to `.agents/.pending-changes.json` for the agent to consume at the start of the next session.

```bash
# Start watcher with 500ms debounce (default)
blublu watch

# Custom debounce: 1000ms, polling every 5 seconds
blublu watch --debounce 1000 --interval 5

# Stop the background watcher process
blublu stop
```

**What it tracks:**
- New, modified, deleted, and renamed source files.
- Ignores: `node_modules/`, `vendor/`, `.git/`, `dist/`, `build/`, `coverage/`, `.next/`, `.cache/`, `__pycache__/`.
- PID file: `.agents/.blublu.pid` (auto-cleaned on stop).
- Output: `.agents/.pending-changes.json` (read by agent at session start; excluded from git via `.gitignore`).

> [!NOTE]
> The watcher is fully deterministic and stateless — it performs no LLM calls, no network requests, and no blueprint writes on its own. It only accumulates metadata for the next agent session to consume.

---

### D. CI/CD Validation with v1.2.0 Distributed Support

The existing GitHub Actions workflows (`blublu-validate.yml`, `blublu-architecture-check.yml`) automatically handle both single-file and distributed modes — no CI configuration changes are required when migrating a project to distributed mode.

