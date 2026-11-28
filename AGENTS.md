<!-- blublu:start -->
## Codebase Architecture & Memory (blublu v2.0.0)
This project uses **blublu** to maintain persistent architectural memory using a 4-level hierarchical blueprint system.

### Mandatory Loading Protocol
1. **ALWAYS read `.agents/codebase-map.md` first** (Level 1 — Global Architecture). This is the global index.
2. **Identify the domain** touched by the current prompt from the Sub-Blueprints Index in Section 5.
3. **Load ONLY `.agents/sub-blueprints/<domain>.md`** (Level 2) for the relevant domain. Never load all domains.
4. **Load `.agents/sub-blueprints/<domain>/<module>.md`** (Level 3) ONLY if making interface/contract-level changes to a specific module.
5. **Level 4 detail** (appended to Level 3 file) is loaded ONLY on explicit user request for implementation details.

### Operational Rules
- Respect registered layer boundaries, export contracts, and dependency flows.
- Record cross-service dependencies with Confidence labels: `Confirmed` (source code evidence) | `Inferred` (pattern) | `Unverified` (docs-only).
- Flag circular dependencies as `[CIRCULAR DEPENDENCY - REVIEW REQUIRED]`.
- When architectural changes occur, update ONLY the blueprint levels you read in this session.
- Never auto-apply destructive blueprint changes from drift detection reports — only report and recommend.

### CLI Tools Available
- `blublu status` — Architecture health summary and mode detection.
- `blublu validate --check-drift` — Drift detection across all modules.
- `blublu analyze <module>` — Hierarchical context for a specific module.
- `blublu dependencies [--module <name>]` — Full dependency map.
- For complete protocols, consult `skills/blublu/SKILL.md`.
<!-- blublu:end -->

