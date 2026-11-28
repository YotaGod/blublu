# Mapping Rules & Depth Guidelines

This reference defines how AI coding agents should map a codebase into `.agents/codebase-map.md` and the hierarchical sub-blueprint system. It provides standards for mapping depth, the 4-level hierarchical architecture, module verification tagging, and directory ignore lists.

---

## 1. Balanced Mapping Depth

Codebase documentation must strike a balance between high-level architectural insight and token efficiency. blublu v2.0.0 uses a **Four-Level Hierarchical Architecture**:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Level 1: Global Architecture  (.agents/codebase-map.md)               │
│  - Project overview, major domains, global tech stack                  │
│  - High-level architecture style, Sub-Blueprints Index                 │
│  - Token budget: 500–700 tokens. ALWAYS read first.                    │
├────────────────────────────────────────────────────────────────────────┤
│ Level 2: Domain Architecture  (.agents/sub-blueprints/<domain>.md)    │
│  - Domain responsibilities, module list, internal dependencies         │
│  - Domain-scoped data flows and public API surface                     │
│  - Token budget: 400–600 tokens. Load ONLY the relevant domain.        │
├────────────────────────────────────────────────────────────────────────┤
│ Level 3: Module Architecture  (.agents/sub-blueprints/<domain>/<mod>) │
│  - Entry points, public interfaces, local/cross-domain dependencies    │
│  - Database entities, verification metadata                            │
│  - Token budget: 300–500 tokens. Load only for interface-level changes.│
├────────────────────────────────────────────────────────────────────────┤
│ Level 4: Detailed Architecture  (section appended to Level 3 file)    │
│  - Algorithm descriptions, state machines, security invariants         │
│  - Load ONLY on explicit user request for implementation details.      │
└────────────────────────────────────────────────────────────────────────┘
```

### Depth Guidelines by Level

#### Level 1: Global Architecture (Always Concise)
- Project name, type, primary language/framework, global tech stack.
- List of major domains/services (names + one-line responsibilities).
- Architecture style (microservices, monolith, event-driven, BFF, etc.).
- Cross-domain dependency topology (high-level Mermaid `graph TD`).
- Sub-Blueprints Index table (for distributed mode projects).
- **Token budget target: 500–700 tokens. If Level 1 exceeds 800 tokens, migrate detail to Level 2.**

#### Level 2: Domain Architecture (Core Focus)
- Domain identity: name, type (service/library/frontend/infra), owning team.
- Domain responsibilities (3–5 bullet points).
- Module Registry for this domain (abbreviated: Module, Path, Responsibility, Status).
- Internal dependency map (Mermaid `graph TD` scoped to this domain).
- Domain-level data flows (request lifecycle, event processing).
- Public API surface (endpoint list or exported interface summary).
- Cross-domain integration points (which Level 1 services this domain calls/emits to).
- **Token budget target: 400–600 tokens.**

#### Level 3: Module Architecture (Selective Inclusion)
- Module identity: name, path, owner, verification status.
- Entry points and bootstrap sequence.
- Public interface: exported functions, classes, events, or HTTP routes (with signatures).
- Local dependencies (what this module imports from within the domain).
- Cross-domain dependencies (external imports).
- Database entities owned by this module.
- Verification metadata: last verified date, verifying agent/tool.
- **Token budget target: 300–500 tokens.**
- **When to create Level 3**: Module has >3 public exports, owns a DB schema, is imported by >5 other modules, or has significant technical debt.

#### Level 4: Detailed Architecture (Optional, On-Demand)
- Algorithm descriptions for non-obvious business logic.
- State machine diagrams for complex workflows.
- Performance constraints and known hotspots.
- Security-sensitive code sections requiring special care.
- Historical context for unusual design decisions (ADR-style rationale).
- **NEVER create Level 4 proactively.** Only when user explicitly asks for implementation details.

---

## 2. Hierarchical Architecture Mapping Protocol (v2.0.0)

blublu v2.0.0 replaces the flat single-file blueprint with an optional hierarchical multi-file system for large projects. Single-file blueprints from v1.0–v1.2 remain fully supported.

### Architecture Modes

| Mode | Root File | Sub-Blueprint Directory | Use When |
| :--- | :--- | :--- | :--- |
| **Single-File** (v1.x compatible) | `.agents/codebase-map.md` | Not present | Projects with ≤40 modules |
| **Distributed** (v1.2+ feature) | `.agents/codebase-map.md` (index) | `.agents/sub-blueprints/<domain>.md` | 10–50 domains |
| **Hierarchical** (v2.0 feature) | `.agents/codebase-map.md` (global index) | `.agents/sub-blueprints/<domain>.md` + `.agents/sub-blueprints/<domain>/<module>.md` | 50+ modules or complex domains |

### Level 1 Content Rules
- Section 5 Module Registry at Level 1 must list DOMAINS (not individual files).
- Each row aggregates an entire domain into a single entry.
- If distributed mode: Section 5 also contains a `Sub-Blueprints Index` table.
- Level 1 NEVER contains per-module function signatures, database column definitions, or API route listings.

### Level 2 Content Rules
- One file per domain. File name must be the domain slug (e.g., `order.md`, `shared-libs.md`).
- Module Registry in Level 2 lists the actual modules within that domain.
- Cross-domain dependencies are recorded with Confidence labels (see Section 6 of update-rules.md).

### Level 3 Content Rules
- One file per module, nested under the domain directory.
- Path: `.agents/sub-blueprints/<domain>/<module-slug>.md`
- Must include a machine-readable metadata block at the top.
- Level 4 is appended as the last section of the Level 3 file (not a separate file).

---

## 3. Verification Status System

Every tracked module in the **Module Registry** MUST carry an explicit status tag:

| Status Tag | Definition & Criteria | When to Assign |
| :--- | :--- | :--- |
| `[Verified]` | Confirmed directly against source code files. File exists, exports match, and dependencies are validated by reading imports. | Assigned when the agent directly inspects the module files on disk and confirms their contents. |
| `[Inferred]` | Deduced from standard framework conventions, file/folder names, or package manifests without full deep file inspection. | Assigned during quick initialization scans when directory naming clearly implies responsibility. |
| `[Unverified]` | Mentioned in legacy comments, documentation, or suggested by naming, but not corroborated or partially ambiguous. | Assigned when a component's exact role or active status is unclear and needs further inspection. |
| `[Stale]` | Previously verified, but underlying source files have undergone modifications since the last verification. | Assigned automatically when git diff or file hashes indicate the module was touched without blueprint synchronization. |

### Status Transition Lifecycle

```
       [Unverified] ──(Partial analysis)──> [Inferred]
             │                                  │
             │        (Deep inspection)         │
             └──────────────────────────────────▼
                                           [Verified]
                                                │
                                    (Source file modified)
                                                ▼
                                             [Stale]
                                                │
                                        (Re-inspected)
                                                ▼
                                           [Verified]
```

- When resolving a task touching a `[Stale]`, `[Inferred]`, or `[Unverified]` module, the agent SHOULD inspect the module and elevate it to `[Verified]`.

---

## 4. Hierarchical Agent Navigation Protocol

AI agents using blublu v2.0.0 MUST follow this loading sequence precisely:

```
User Prompt Received
       │
       ▼
Step 1: READ .agents/codebase-map.md (Level 1 — Global Architecture)
       │
       ├─ Is this a global/cross-domain question?
       │  YES → Answer from Level 1. STOP. Do not load sub-blueprints.
       │
       ▼
Step 2: IDENTIFY domain(s) touched by the prompt
       │
       ├─ No sub-blueprints directory? → Work with Level 1 only. STOP.
       │
       ▼
Step 3: LOAD .agents/sub-blueprints/<domain>.md (Level 2)
       │  Load ONLY the matching domain. Never load all domains.
       │
       ├─ Are changes limited to internal implementation?
       │  YES → Work from Level 2. STOP.
       │
       ▼
Step 4 (Conditional): LOAD .agents/sub-blueprints/<domain>/<module>.md (Level 3)
       │  ONLY if: change touches a public interface/API, exported contract,
       │  database schema owned by this module, or cross-domain dependency.
       │
       ▼
Step 5 (Explicit Only): READ Level 4 section in Level 3 file
       ONLY when user explicitly asks for implementation details.
```

### Navigation Rules (Mandatory)

1. **Always start at Level 1.** No exceptions, even if you think you know the codebase.
2. **Load the minimum sufficient context.** Each additional level loaded = tokens consumed permanently for that session.
3. **Never load all sub-blueprints simultaneously.** This violates the entire purpose of hierarchical mapping.
4. **Level 3 is rare.** Most day-to-day tasks (bug fixes, feature additions, refactors) are fully solvable from Level 1 + Level 2.
5. **Level 4 is on-demand only.** Never load it preemptively.
6. **After completing a task, update ONLY the levels you read.** Do not cascade updates to unread levels.
7. **Never infer cross-domain dependencies without evidence.** Only record what is backed by source code (see update-rules.md Section 6).

---

## 5. Ignore Patterns (Scanning Filter)

To prevent context exhaustion and irrelevant noise, AI agents MUST NEVER scan or index the following directories and file patterns:

### Package Managers & External Dependencies
- `node_modules/`
- `vendor/`
- `.pnpm-store/`
- `packages/*/node_modules/`
- `bower_components/`
- `jspm_packages/`

### Build Artifacts, Bundles & Compilers
- `dist/`, `build/`, `out/`, `target/`, `bin/`, `obj/`
- `.next/`, `.nuxt/`, `.output/`, `.svelte-kit/`, `.astro/`
- `.vuepress/dist/`, `.docusaurus/`
- `*.min.js`, `*.min.css`, `*.bundle.js`, `*.map`
- `*.pyc`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`
- `*.class`, `*.jar`, `*.war`
- `*.wasm`, `*.dylib`, `*.so`, `*.dll`, `*.exe`

### Version Control & Agent Tracking
- `.git/`, `.svn/`, `.hg/`
- `.agents/scratch/` (Temporary agent notes; do not index as source)
- `.agents/.pending-changes.json`, `.agents/.blublu.pid`, `.agents/.cache_scan.json` (Runtime artifacts)

### Caches, Temporary Files & Logs
- `.cache/`, `.turbo/`, `.parcel-cache/`
- `tmp/`, `temp/`, `*.tmp`
- `*.log`, `npm-debug.log*`, `yarn-debug.log*`, `yarn-error.log*`, `pnpm-debug.log*`
- `.DS_Store`, `Thumbs.db`

### Test Coverage & Benchmarks
- `coverage/`, `.nyc_output/`
- `test-results/`
- `playwright-report/`, `cypress/videos/`, `cypress/screenshots/`

### Media & Binary Assets
- Images: `*.png`, `*.jpg`, `*.jpeg`, `*.gif`, `*.webp`, `*.svg`, `*.ico`
- Audio/Video: `*.mp3`, `*.mp4`, `*.wav`, `*.mov`, `*.webm`
- Fonts: `*.woff`, `*.woff2`, `*.ttf`, `*.eot`, `*.otf`
- Documents: `*.pdf`, `*.zip`, `*.tar.*`, `*.gz`, `*.7z`

### Lockfiles & Secrets
- **Lockfiles**: Treat `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `Cargo.lock`, `composer.lock`, and `poetry.lock` as opaque. Read root manifests (`package.json`, `Cargo.toml`, `pyproject.toml`) for dependencies instead of parsing multi-megabyte lockfiles.
- **Environment & Credential Files**: `.env`, `.env.*`, `*.pem`, `*.key`, `*.cert`, `credentials.json`, `id_rsa`. Never index or record secrets in the blueprint!

---

## 6. Large Monorepo & Token Budget Mitigations

When maintaining codebase blueprints for large repositories or multi-package monorepos:

1. **The 40-Module Threshold Warning**:
   If the **Module Registry** (Section 5) grows beyond **40 rows**, the blueprint risks consuming excessive context window capacity (> 2,500 tokens).
2. **Domain Boundary Aggregation**:
   When the threshold is reached, agents MUST aggregate lower-level subdirectories into high-level domain packages:
   - *Example*: Instead of registering `apps/billing/controllers`, `apps/billing/services`, `apps/billing/repositories`, and `apps/billing/validators` as 4 discrete rows, collapse them into a single module entry:
     ```markdown
     | `BillingApp` | `apps/billing` | Invoicing, subscription state machine, and payment callbacks | `SharedDb`, `SharedAuth` | [Verified] |
     ```
3. **Hierarchical Blueprint System (v2.0.0 Solution)**:
   For repositories with more than 15–50 modules, use the full Hierarchical Architecture:
   - **Level 1** (`.agents/codebase-map.md`): Global index only. Domains aggregated into single rows. Max 700 tokens.
   - **Level 2** (`.agents/sub-blueprints/<domain>.md`): Per-domain detail. Load only the touched domain.
   - **Level 3** (`.agents/sub-blueprints/<domain>/<module>.md`): Per-module detail. Load only for interface-level changes.
   - **Progressive Context Loading Rule**: Agents are strictly FORBIDDEN from reading all sub-blueprints at task start.

---

## 7. Mermaid Diagram Manipulation Protocol

When updating Section 6 (Dependency Mapping), AI agents MUST follow these precise syntax rules to prevent corrupting the diagram:

1. **Directional Header**:
   Always begin with `graph TD` (top-down) or `graph LR` (left-to-right). Never omit or alter the header.
2. **Safe Alphanumeric Node Identifiers**:
   Node identifiers MUST be alphanumeric PascalCase or camelCase without slashes or hyphens (e.g., `UserModule`, `AuthService`, `PaymentAPI`).
3. **Mandatory Quoting of Node Labels**:
   Always wrap human-readable display labels and file paths in double quotes inside brackets:
   ```mermaid
   graph TD
       Auth["src/modules/auth"] --> User["src/modules/user"]
       Billing["src/modules/billing"] --> StripeAPI(("Stripe API"))
   ```
4. **Standard Arrow Operators**:
   - Use `-->` for direct compile-time or runtime code dependencies (imports/calls).
   - Use `-.->` for asynchronous, event-driven, or optional dependencies.
   - Use `==>` for primary critical execution paths.
5. **Preserve Diagram Fences**:
   Never delete the opening ` ```mermaid ` or closing ` ``` ` fences when adding or removing edges.
