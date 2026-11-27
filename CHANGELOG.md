# Changelog

All notable changes to the **blublu** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-11-27

### Added
- **Distributed Sub-Blueprints Architecture (`.agents/sub-blueprints/`)**:
  - Sub-blueprint schema specification (`skills/blublu/references/sub-blueprint-template.md`).
  - `Sub-Blueprints Index` integration in Section 5 of `.agents/codebase-map.md`.
  - Context-Aware / Progressive Loading rule for AI agents (root index first, zero premature bulk loading).
- **Unified Standalone CLI Engine (`scripts/codsblu.py`)**:
  - `codsblu init [--distributed]`: Instant bootstrap of single-file or distributed architecture.
  - `codsblu status`: Comprehensive architecture health summary, mode detection, and background watcher status.
  - `codsblu validate`: End-to-end multi-blueprint validation, broken path check, and orphaned sub-blueprint detection.
  - `codsblu migrate --to-distributed`: Intelligent automated decomposition of single-file maps into domain sub-blueprints.
  - `codsblu watch` & `codsblu stop`: Background filesystem watcher lifecycle management.
- **Cross-Platform CLI Wrappers**:
  - `scripts/codsblu` (POSIX Bash wrapper for Linux & macOS).
  - `scripts/codsblu.ps1` & `scripts/codsblu.cmd` (PowerShell and Batch wrappers for Windows).
- **Local Filesystem Change Watcher (`scripts/watcher.py`)**:
  - Polling event loop with configurable debounce delay (default 2000ms).
  - Deterministic event queue in `.agents/.pending-changes.json`.
  - Process PID tracking in `.agents/.codsblu.pid`.
  - Strict security guardrail: strictly zero automated remote paid LLM API calls.
- **Validator Upgrade for Distributed Mode (`scripts/validate-blueprint.py`)**:
  - Auto-discovery of registered sub-blueprints and cross-validation against physical disk files.
  - Orphaned sub-blueprint detection (`.agents/sub-blueprints/*.md` unindexed in root).
- **Test Fixtures & Scenarios**:
  - `tests/fixtures/distributed-app/`: Multi-domain monorepo fixture (`apps/api` and `apps/web`).
  - `tests/scenarios/distributed-architecture.md`: Progressive loading and sub-blueprint index tests.
  - `tests/scenarios/cli-watcher.md`: CLI status, watcher PID, and debounce verification tests.

---

## [1.1.0] - 2026-11-27

### Added
- **Advanced Filesystem Fallback Scanner (`scripts/scanner.py`)**:
  - Dual-mode change detector automatically identifying Git vs. non-Git environments.
  - Sub-second Git integration (`git status --short`, `git diff --name-only`) for Git repos.
  - Recursive filesystem change detection with metadata/mtime/hash caching (`.agents/.cache_scan.json`) when Git is unavailable.
  - Strict directory ignore rules and recursive symlink protection (`follow_symlinks=False`).
- **Automated Mermaid Diagram Validator (`scripts/validate-blueprint.py`)**:
  - Validates diagram declarations (`graph`, `flowchart`, `sequenceDiagram`, `classDiagram`, `erDiagram`, etc.).
  - Detects unbalanced brackets, malformed arrow syntax (`->` vs `-->`), and unquoted label characters.
  - **Graceful Markdown Table Fallback**: Generates structured table recommendations (`| Source Module | Target Module | Relationship |`) if Mermaid syntax is defective.
- **Staleness & Architecture Drift Detection (`--check-staleness`)**:
  - Cross-references modified source files with registered module paths to detect drift before commits.
- **Official GitHub Actions CI Workflows**:
  - `.github/workflows/codsblu-validate.yml`: Continuous validation gate for pull requests and pushes.
  - `.github/workflows/codsblu-architecture-check.yml`: Flags source code changes without architectural blueprint synchronization.
- **Product Roadmap (`docs/roadmap.md`)**:
  - Comprehensive milestone architecture from v1.0.0 through v2.0.0.
- **Test Fixtures & Scenarios**:
  - `tests/fixtures/non-git-app/`: Standalone project fixture for filesystem scanner testing.
  - `tests/fixtures/malformed-mermaid/`: Corrupted Mermaid fixture verifying error detection and table fallback.
  - `tests/scenarios/v1.1.0-validation.md`: End-to-end verification scenario guide.

---

## [1.0.0] - 2026-11-27

### Added
- **Core Agent Skill (`skills/blublu/SKILL.md`)**:
  - Open Standard Agent Skill definition with YAML metadata.
  - Implemented 7 Core Principles: Read Before Coding, Understand Before Modifying, Incremental Mapping, Update After Coding, Verify Before Finishing, Source Code Is Truth, and Token Efficiency.
  - Defined strict Automatic Lifecycle (`BEFORE TASK`, `DURING TASK`, `AFTER TASK`).
  - Added support for explicit commands: `initialize`, `update`, `rebuild`, `validate`, `impact [module]`, and `status`.
- **Architectural Blueprint Template (`skills/blublu/references/blueprint-template.md`)**:
  - Standardized 15-section schema for `.agents/codebase-map.md`.
  - Structured Module Registry table format (`Module`, `Path`, `Responsibility`, `Dependencies`, `Status`).
  - Integrated Mermaid diagram syntax for visual dependency topologies and data flow tracking.
- **Balanced Mapping Rules (`skills/blublu/references/mapping-rules.md`)**:
  - Three-tier depth guidelines: Level 1 (System Topology), Level 2 (Module & Boundaries), and Level 3 (Critical Invariants).
  - Four-state module verification tag system: `[Verified]`, `[Inferred]`, `[Unverified]`, and `[Stale]`.
  - Comprehensive scanning ignore lists covering package caches, build outputs, version control, and sensitive credentials.
- **Update & Synchronization Rules (`skills/blublu/references/update-rules.md`)**:
  - Git-aware diffing workflows leveraging `git status --short` and `git diff --stat`.
  - Change Trigger Matrix distinguishing architectural mutations from internal code refactors.
  - Graceful fallback routines for non-Git working trees.
- **Validation Engine Rules (`skills/blublu/references/validation-rules.md`)**:
  - Self-healing consistency check procedures for AI agents.
  - Automated detection of broken file paths, unmapped directories, stale routes, and orphaned modules.
  - Mathematical formula for Verification Ratio and three-tier health status classification (`Healthy`, `Drift Detected`, `Needs Rebuild`).
- **Project Infrastructure & Documentation**:
  - MIT License and comprehensive `.gitignore` rules.
  - Architectural whitepaper (`docs/architecture.md`), installation guide (`docs/installation.md`), and usage manual (`docs/usage.md`).
