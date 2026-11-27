# Contributing to blublu

Thank you for your interest in improving **blublu — AI Codebase Memory & Architecture Tracking System**! We welcome contributions from developers, researchers, and AI agent engineers.

---

## Code of Conduct & Contribution Philosophy

- **Respect the Ground Truth**: In blublu, source code on disk is always the ultimate truth. Contributions to documentation, skills, or rules must reflect verifiable implementation realities.
- **Token Efficiency First**: Every rule, reference, or prompt added to blublu is read by AI agents on repeated invocations. We prioritize concise, dense, high-signal information over verbose prose.
- **Non-Destructive Operations**: Never introduce scripts or agent commands that execute destructive git operations (`git reset --hard`, `git clean -fd`) or leak sensitive environment keys.

---

## How You Can Contribute

### 1. Reporting Bugs & Inconsistencies
If you encounter an issue where an agent misinterprets a rule, generates invalid blueprint markdown, or hallucinates architectural components:
- Search existing GitHub Issues to check if the behavior was already reported.
- Open a new issue with a clear reproduction case:
  - Agent platform used (e.g., Antigravity, Claude Code, Codex).
  - The repository structure being mapped.
  - The unexpected blueprint output or validation error.

### 2. Enhancing Skills & Operational References
All agent skills reside in `skills/blublu/`. When proposing changes to `SKILL.md` or files in `references/`:
- Maintain valid Agent Skills Open Standard YAML frontmatter in `SKILL.md`.
- Keep rules deterministic and unambiguous for LLM reasoning engines.
- Ensure all 15 sections of the blueprint template remain backward-compatible.
- Run local validation checks before submitting your pull request.

### 3. Adding Platform Integrations & Installers
We welcome additional installers or sidecar hooks for emerging agent platforms:
- Follow existing patterns established in `docs/installation.md`.
- Ensure scripts support dry-run flags (`--dry-run`) and both Project Scope and Global Scope installations.
- Keep installation scripts cross-platform (Bash for Linux/macOS and PowerShell for Windows).

---

## Development & Local Testing Workflow

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/blublu.git
   cd blublu
   ```

2. **Verify Integrity of Skill Files**:
   - Confirm that all markdown links between `SKILL.md` and `references/*.md` are valid relative paths or standard file URI schemas.
   - Verify that no placeholders, stub comments (`// TODO`), or hardcoded secrets exist in the codebase.

3. **Test with Sample Workspaces**:
   - Test running `initialize` and `validate` against a sample repository.
   - Inspect `.agents/codebase-map.md` to confirm all 15 sections format cleanly without markdown syntax errors.

---

## Pull Request Guidelines

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes with clear, descriptive commit messages following Conventional Commits (e.g., `feat:`, `fix:`, `docs:`, `refactor:`).
3. Ensure `CHANGELOG.md` is updated under the `[Unreleased]` section.
4. Submit the Pull Request with a summary of changes, motivation, and test steps conducted.
