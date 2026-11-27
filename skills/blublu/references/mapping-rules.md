# Mapping Rules & Depth Guidelines

This reference defines how AI coding agents should map a codebase into `.agents/codebase-map.md`. It provides standards for mapping depth, module verification tagging, and directory ignore lists.

---

## 1. Balanced Mapping Depth

Codebase documentation must strike a balance between high-level architectural insight and token efficiency. We standardize on **Three Levels of Mapping Depth**:

```
┌────────────────────────────────────────────────────────┐
│ Level 1: System & Topology (Always Include)            │
│  - Application type, runtime environment, entry points  │
│  - Architectural style, high-level directory tree      │
├────────────────────────────────────────────────────────┤
│ Level 2: Module & Component Boundaries (Core Focus)    │
│  - First-party modules, paths, core responsibilities   │
│  - Intersystem dependencies, public interfaces         │
├────────────────────────────────────────────────────────┤
│ Level 3: Critical Implementation Details (Selective)   │
│  - Domain models, database schemas, primary data flows │
│  - External integrations, crucial business invariants  │
└────────────────────────────────────────────────────────┘
```

### Depth Guidelines by Level

#### Level 1: System Architecture (Always Map)
- Overall runtime and platform targets (e.g., Node.js v20, Go 1.22, Python 3.11, Next.js App Router).
- Primary bootstrap files and runtime entry points (CLI bin, HTTP listener, queue worker, lambda handler).
- Top-level directory structure (limit depth to 2–3 levels).

#### Level 2: Module & Boundary Mapping (The Core of the Blueprint)
- Map every distinct functional domain or directory boundary in `Module Registry`.
- Identify explicit inter-module dependencies (who imports from whom).
- Specify the public responsibility of each module in 1–2 dense sentences.

#### Level 3: Critical Logic & Contracts (Selective Inclusion)
- **INCLUDE**:
  - Primary API route endpoints and method verbs.
  - Core database entities and relational foreign key relationships.
  - Critical end-to-end data flows (e.g. login, payment checkout, webhook processing).
  - External 3rd-party services and required environment keys.
  - Hard business invariants (e.g., "tenants cannot share data", "refunds require manager approval").
- **DO NOT INCLUDE (Micro-Noise / Slop)**:
  - Private helper functions or utility internals.
  - Local variables, loop counters, and transient state.
  - CSS classes, layout styling, and minor markup adjustments.
  - Complete copies of raw code snippets, interfaces, or type definitions.
  - Low-level unit test names or boilerplate getters and setters.

---

## 2. Verification Status System

Every tracked module in the **Module Registry** MUST carry an explicit status tag:

| Status Tag | Definition & Criteria | When to Assign |
| :--- | :--- | :--- |
| `[Verified]` | Confirmed directly against source code files. File exists, exports match, and dependencies are validated by reading imports. | Assigned when the agent directly inspects the module files on disk and confirms their contents. |
| `[Inferred]` | Deduced from standard framework conventions, file/folder names, or package manifests without full deep file inspection. | Assigned during quick initialization scans when directory naming clearly implies responsibility (e.g., `src/routes/auth.ts`). |
| `[Unverified]` | Mentioned in legacy comments, documentation, or suggested by naming, but not corroborated or partially ambiguous. | Assigned when a component's exact role or active status is unclear and needs further inspection before trusting. |
| `[Stale]` | Previously verified, but underlying source files have undergone modifications, renames, or deletions since the last verification. | Assigned automatically when git diff or file hashes indicate the module was touched without blueprint synchronization. |

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

## 3. Ignore Patterns (Scanning Filter)

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

## 4. Large Monorepo & Token Budget Mitigations

When maintaining codebase blueprints for large repositories or multi-package monorepos:

1. **The 40-Module Threshold Warning**:
   If the **Module Registry** (Section 5) grows beyond **40 rows**, the blueprint risks consuming excessive context window capacity (> 2,500 tokens).
2. **Domain Boundary Aggregation**:
   When the threshold is reached, agents MUST aggregate lower-level subdirectories into high-level domain packages:
   - *Example*: Instead of registering `apps/billing/controllers`, `apps/billing/services`, `apps/billing/repositories`, and `apps/billing/validators` as 4 discrete rows, collapse them into a single module entry:
     ```markdown
     | `BillingApp` | `apps/billing` | Invoicing, subscription state machine, and payment callbacks | `SharedDb`, `SharedAuth` | [Verified] |
     ```
3. **Sub-Blueprint Staging & Progressive Loading**:
   For repositories with more than 30–50 modules, use Codsblu v1.2.0 **Distributed Blueprints**:
   - The root `.agents/codebase-map.md` serves strictly as the global index and architecture topology (Sections 1–4, 6, 8–15), with Section 5 maintaining high-level domain entries and the `Sub-Blueprints Index`.
   - Granular submodules, domain flows, and domain tables are stored in `.agents/sub-blueprints/<domain>.md` conforming to [sub-blueprint-template.md](sub-blueprint-template.md).
   - **Progressive Context Loading Rule**: Agents are strictly FORBIDDEN from reading all sub-blueprints at task start. Agents must read `.agents/codebase-map.md` first, resolve which domain is affected by the prompt, and selectively load *only* that domain's sub-blueprint into context.

---

## 5. Mermaid Diagram Manipulation Protocol

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
   Never delete the opening ```` ```mermaid ```` or closing ```` ``` ```` fences when adding or removing edges.

