# Installation & Platform Integration Guide

This guide provides instructions for installing and integrating **blublu** across different operating systems (Linux, macOS, Windows) and agent environments (Google Antigravity, Anthropic Claude Code, OpenAI Codex).

---

## 1. Installation Scopes: Project vs. Global

blublu supports two deployment scopes depending on your team's workflow:

| Scope | Location | Use Case |
| :--- | :--- | :--- |
| **Project Scope** *(Recommended)* | In the repository: `skills/blublu/` and `.agents/codebase-map.md` | Team repositories where multiple developers and AI agents collaborate on the same shared architecture map. Checked into Git. |
| **Global Scope** | User home config directory: `~/.gemini/antigravity/skills/` or `~/.claude/skills/` | Personal machine setup where you want blublu active across all local repositories automatically without adding files to git. |

---

## 2. Automated Installation

### A. Linux & macOS (Bash)

The shell installer automatically detects installed AI agents and places skill files in the appropriate directories.

```bash
# Install to current repository (Project Scope)
curl -fsSL https://raw.githubusercontent.com/YotaGod/blublu/main/install.sh | bash

# Install globally for all repositories
curl -fsSL https://raw.githubusercontent.com/YotaGod/blublu/main/install.sh | bash -s -- --scope global

# Target a specific agent platform
curl -fsSL https://raw.githubusercontent.com/YotaGod/blublu/main/install.sh | bash -s -- --agent antigravity --scope global
```

### B. Windows (PowerShell)

```powershell
# Install to current repository (Project Scope)
iwr -useb https://raw.githubusercontent.com/YotaGod/blublu/main/install.ps1 | iex

# Install globally for all repositories
& { iwr -useb https://raw.githubusercontent.com/YotaGod/blublu/main/install.ps1 } -Scope global

# Target a specific agent platform
& { iwr -useb https://raw.githubusercontent.com/YotaGod/blublu/main/install.ps1 } -Agent antigravity -Scope global
```

### Installer CLI Flags

| Flag (Bash) | Parameter (PowerShell) | Description | Default |
| :--- | :--- | :--- | :--- |
| `--scope <project\|global>` | `-Scope <project\|global>` | Target installation scope | `project` |
| `--agent <all\|antigravity\|claude\|codex>` | `-Agent <all\|antigravity\|claude\|codex>` | Target agent environment | `all` (detected) |
| `--dry-run` | `-DryRun` | Simulates install without writing files | `false` |
| `--upgrade` | `-Upgrade` | Overwrites existing blublu skill files with latest version | `false` |

---

## 3. Platform-Specific Agent Configuration

### A. Google Antigravity

Antigravity natively discovers Agent Skills conforming to the Agent Skills Open Standard.

- **Project Scope**:
  Place the skill inside your workspace:
  ```
  my-project/
  └── skills/
      └── blublu/
          ├── SKILL.md
          └── references/
  ```
- **Global Scope**:
  Place the skill inside your global Antigravity config:
  ```
  ~/.gemini/antigravity/skills/blublu/    # Linux / macOS
  %USERPROFILE%\.gemini\antigravity\skills\blublu\   # Windows
  ```
- **Agent Rule Integration**:
  To ensure Antigravity always reads the blueprint before coding tasks, add this snippet to your `.gemini/antigravity/rules.md` or workspace rules:
  ```markdown
  Before performing any architectural modifications, reading or editing code,
  always inspect `.agents/codebase-map.md`. After completing tasks with architectural
  impact, run the blublu update protocol.
  ```

### B. Anthropic Claude Code

Claude Code reads instructions from `CLAUDE.md` and discovers custom tools and skills from `~/.claude/skills/`.

- **Project Scope**:
  Add the following directive to your project's `CLAUDE.md`:
  ```markdown
  ## Architecture & Codebase Memory (blublu)
  This project uses blublu to maintain an architectural map in `.agents/codebase-map.md`.
  - Always read `.agents/codebase-map.md` before refactoring or adding features.
  - Follow instructions in `skills/blublu/SKILL.md` when executing `initialize`, `update`, or `validate`.
  ```
- **Global Scope**:
  Copy the `skills/blublu` folder into `~/.claude/skills/blublu`.

### C. OpenAI Codex & Generic Agents

Generic agents look for instruction files such as `AGENTS.md` in the workspace root.

- Add the following directive to your `AGENTS.md`:
  ```markdown
  # Codebase Memory System
  Refer to `.agents/codebase-map.md` for project architecture, conventions, and module boundaries.
  Consult `skills/blublu/SKILL.md` for update and validation rules.
  ```

---

## 4. Verifying the Installation

To verify that blublu is recognized by your AI coding agent:
1. Open an agent session in your workspace.
2. Send the prompt:
   > *"Run blublu status"*
3. The agent should respond by inspecting `.agents/codebase-map.md` or indicating that the blueprint is ready to be initialized via `blublu initialize`.
