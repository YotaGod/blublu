# Changelog

All notable changes to the **blublu** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
