---
name: blublu
description: Maintains a persistent, verified architectural blueprint of a software codebase. Use when analyzing, creating, modifying, debugging, refactoring, or documenting a project. Reads the existing blueprint before code-related work and updates it after architectural changes.
license: MIT
metadata:
  version: "1.2.0"
  author: "blublu"
---

# blublu: AI Codebase Memory & Architecture Tracking System

`blublu` acts as the persistent cognitive map and architectural memory for AI coding agents operating across multiple sessions. It maintains `.agents/codebase-map.md`, an accurate, token-efficient, and verified blueprint of the repository.

---

## 1. Core Principles

1. **Read Before Coding**
   Before touching any code, the agent MUST read `.agents/codebase-map.md` to load the current system architecture, active module boundaries, data flows, and project conventions into its context.

2. **Understand Before Modifying**
   Evaluate how planned changes ripple through dependencies. Never modify a component in isolation without consulting its registered consumers and dependencies.

3. **Incremental Mapping**
   Keep documentation fast and token-efficient. Do not rebuild the entire blueprint for localized changes; update only the modules and sections affected by recent modifications.

4. **Update After Coding**
   Whenever an architectural change is made (new files, deleted files, modified module contracts, added dependencies, altered routes, or schema changes), synchronize `.agents/codebase-map.md` before concluding the task.

5. **Verify Before Finishing**
   Every claim in the blueprint must be verified against real source files on disk. Confirm file paths exist, exported symbols match, and module statuses accurately reflect verification levels.

6. **Source Code Is Truth**
   When discrepancies arise between existing documentation and source code, source code wins. Update the blueprint to match the reality of the implementation.

7. **Token Efficiency**
   The blueprint is read on every subsequent agent run. Keep explanations dense, structured, and factual. Prefer tables, lists, and concise flow descriptors over verbose prose. Avoid dumping raw code snippets or trivial implementation details.

8. **Context-Aware / Progressive Loading**
   In distributed architecture repositories (`.agents/sub-blueprints/`), the agent MUST read the root index (`.agents/codebase-map.md`) first. The agent is strictly FORBIDDEN from loading all sub-blueprints into context simultaneously. Only read the specific `.agents/sub-blueprints/<domain>.md` corresponding to the domain touched by the prompt.

---

## 2. Operating Modes

`blublu` operates in two complementary modes: **Automatic Lifecycle** (ambient guardrails during code tasks) and **Explicit Intents** (direct commands invoked by the user or agent).

### A. Automatic Lifecycle

```
[Task Initiated]
       │
       ▼
┌─────────────────────────┐
│       BEFORE TASK       │ ──> Check for .agents/codebase-map.md
│     (Pre-execution)     │     • Exists: Read relevant sections into context.
└─────────────────────────┘     • Missing: Run initial discovery or prompt user.
       │
       ▼
┌─────────────────────────┐
│       DURING TASK       │ ──> Implement user request while observing module
│       (Execution)       │     boundaries, conventions, and dependencies.
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│       AFTER TASK        │ ──> Run `git status` / inspect file diffs.
│    (Post-execution)     │     • Architectural change detected? Update blueprint.
└─────────────────────────┘     • Run verification check on touched entries.
```

#### Detailed Lifecycle Steps:
- **BEFORE TASK (Pre-execution)**:
  1. Inspect whether `.agents/codebase-map.md` exists.
  2. If present, read the **Architecture Overview**, **Module Registry**, **Project Conventions**, and the specific modules relevant to the prompt.
  3. If absent, identify whether the current workspace is initialized. If starting a new project or onboarding an existing one, initialize the blueprint before major restructuring.
- **DURING TASK (Execution)**:
  1. Respect registered architectural boundaries, import conventions, and database patterns.
  2. Note any created, moved, renamed, or deleted files for the post-task update phase.
- **AFTER TASK (Post-execution)**:
  1. Run git diff or file inspection to see altered paths.
  2. Classify if changes are *architectural* (structural, dependency, public API, schema) or *internal* (pure private bugfix or refactor within existing contracts).
  3. If architectural, update affected sections in `.agents/codebase-map.md` and refresh `Mapping Health`.

---

### B. Explicit Commands & Intents

When the user or prompt specifically requests a `blublu` action, execute the corresponding protocol:

| Intent / Command | Trigger Scenario | Action Protocol |
| :--- | :--- | :--- |
| `initialize` | First-time setup on repository | Run directory scan, identify frameworks/entry points, populate `.agents/codebase-map.md` using [blueprint-template.md](file:///skills/blublu/references/blueprint-template.md). |
| `update` | Architectural changes made | Run Git-aware diff analysis and update only modified modules and affected flows per [update-rules.md](file:///skills/blublu/references/update-rules.md). |
| `rebuild` | Drastic drift or complete rework | Re-scan the full project following [mapping-rules.md](file:///skills/blublu/references/mapping-rules.md) and generate a fresh blueprint from scratch. |
| `validate` | Quality assurance & audit | Cross-check all file paths, module entries, and dependencies against filesystem using [validation-rules.md](file:///skills/blublu/references/validation-rules.md). Report discrepancies. |
| `impact [module]` | Pre-refactoring risk evaluation | Look up target module in **Module Registry** and **Dependency Mapping**. Trace all upstream consumers, data flows, and external integrations to provide a blast-radius report. |
| `status` | Brief architectural overview | Report blueprint health status, last updated timestamp, total tracked modules, and verification ratio from Section 15. |

---

## 3. Operational References

Detailed specifications are modularized in the `references/` directory. Consult the appropriate reference for specific procedures:

- **[Blueprint Template](file:///skills/blublu/references/blueprint-template.md)**: Standard 15-section schema for `.agents/codebase-map.md`. Includes guidelines for omitting irrelevant sections (e.g. API or Database for CLI apps).
- **[Mapping Rules](file:///skills/blublu/references/mapping-rules.md)**: Depth guidelines (Levels 1–3), status tag definitions (`[Verified]`, `[Inferred]`, `[Unverified]`, `[Stale]`), and comprehensive ignore rules.
- **[Update Rules](file:///skills/blublu/references/update-rules.md)**: Decision matrix for architectural vs. non-architectural changes, Git-aware inspection workflows, and non-Git fallback procedures.
- **[Validation Rules](file:///skills/blublu/references/validation-rules.md)**: Audit checklists, broken reference checks, stale entry pruning, and health score calculations.

---

## 4. Safety & Integrity Rules

1. **Zero Secret Leakage**
   NEVER write passwords, API keys, JWT secrets, private tokens, connection strings with embedded credentials, or private certificate contents into `.agents/codebase-map.md`. Replace all secrets with descriptive placeholders (e.g., `process.env.STRIPE_SECRET_KEY`).

2. **No Destructive Git Operations**
   When executing Git commands to inspect changes (`git status`, `git diff`), NEVER execute mutating or destructive Git commands like `git reset --hard`, `git clean -fd`, `git checkout .`, `git restore .`, or `git push --force`.

3. **No Ungrounded Assumptions**
   Do not guess framework configurations or architectural layers. If an entry point or purpose cannot be definitively determined from source code, tag it with `[Unverified]` or `[Inferred]` until confirmed.

4. **Directory Isolation**
   All `blublu` architectural state MUST reside within `.agents/codebase-map.md`. Do not scatter miscellaneous tracking files throughout source directories.
