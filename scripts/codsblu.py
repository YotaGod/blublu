#!/usr/bin/env python3
"""
Codsblu (blublu) v1.2.0 — Unified CLI Engine
Autonomous codebase memory management, validation, status reporting, migration,
and local filesystem watcher orchestration.

Dependencies: Pure Python 3 standard library.
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    import scanner
except ImportError:
    scanner = None

try:
    import watcher
except ImportError:
    watcher = None


def resolve_project_root(path_str: str = ".") -> Path:
    p = Path(path_str).resolve()
    if p.is_file() and p.name == "codebase-map.md":
        return p.parent.parent if p.parent.name == ".agents" else p.parent
    return p


def get_blueprint_path(root_path: Path) -> Path:
    return root_path / ".agents" / "codebase-map.md"


def get_sub_blueprints_dir(root_path: Path) -> Path:
    return root_path / ".agents" / "sub-blueprints"


# ------------------------------------------------------------------------------
# Command: init
# ------------------------------------------------------------------------------
def cmd_init(args):
    root = resolve_project_root(args.path)
    blueprint = get_blueprint_path(root)
    sub_dir = get_sub_blueprints_dir(root)

    if blueprint.is_file() and not args.force:
        print(f"[INFO] Blueprint already exists at '{blueprint}'. Use --force to re-initialize.")
        return 0

    blueprint.parent.mkdir(parents=True, exist_ok=True)
    proj_name = root.name

    template_file = CURRENT_DIR / ".." / "skills" / "blublu" / "references" / "blueprint-template.md"
    content = ""
    if template_file.is_file():
        raw_text = template_file.read_text(encoding="utf-8")
        # Extract markdown block
        match = re.search(r"```markdown\s*\n(.*?)```", raw_text, re.DOTALL)
        if match:
            content = match.group(1).replace("[Project Name]", proj_name)

    if not content:
        content = f"""# Codebase Blueprint: {proj_name}

> Auto-generated and maintained by **Codsblu (blublu)**. Source code is the ultimate truth.

---

## 1. Project Overview
- **Name**: {proj_name}
- **Core Purpose**: Initialized architectural blueprint.
- **Primary Tech Stack**: Auto-detecting...
- **Target Platform**: Standard Runtime

---

## 2. Entry Points
| Entry Point | File Path | Type | Purpose / Trigger |
| :--- | :--- | :--- | :--- |

---

## 3. Directory Structure
```
{proj_name}/
```

---

## 4. Architecture Overview
- **Architectural Style**: Modular Architecture

---

## 5. Module Registry
| Module | Path | Responsibility | Dependencies | Status |
| :--- | :--- | :--- | :--- | :--- |

---

## 6. Dependency Mapping
```mermaid
graph TD
```

---

## 7. Main Data Flows

---

## 8. API Mapping
*N/A*

---

## 9. Database Mapping
*N/A*

---

## 10. External Integrations
*N/A*

---

## 11. Project Conventions

---

## 12. Important Business Rules

---

## 13. Known Limitations & Technical Debt

---

## 14. Recent Architectural Changes
- **{datetime.now(timezone.utc).strftime('%Y-%m-%d')}**: Initialized Codsblu architectural blueprint.

---

## 15. Mapping Health
- **Last Updated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
- **Agent / Tool**: Codsblu v1.2.0
- **Health Status**: Healthy
- **Total Tracked Modules**: 0
- **Verification Ratio**: 100%
"""

    if args.distributed:
        sub_dir.mkdir(parents=True, exist_ok=True)
        # Inject Sub-Blueprints Index into Section 5
        index_table = """
### Sub-Blueprints Index (Distributed Mode)
| Domain / Service | Sub-Blueprint Path | Scope / Root Path | Status |
| :--- | :--- | :--- | :--- |
"""
        content = content.replace("## 6. Dependency Mapping", index_table + "\n---\n\n## 6. Dependency Mapping")
        print(f"✔ Initialized distributed sub-blueprints directory at '{sub_dir}'.")

    blueprint.write_text(content, encoding="utf-8")
    mode_desc = "Distributed Mode" if args.distributed else "Single-File Mode"
    print(f"✔ Successfully initialized {mode_desc} at '{blueprint}'.")
    return 0


# ------------------------------------------------------------------------------
# Command: status
# ------------------------------------------------------------------------------
def cmd_status(args):
    root = resolve_project_root(args.path)
    blueprint = get_blueprint_path(root)
    sub_dir = get_sub_blueprints_dir(root)

    print("=" * 60)
    print(" Codsblu (blublu) v1.2.0 — Architecture Status")
    print("=" * 60)
    print(f"Project Root:       {root}")

    if not blueprint.is_file():
        print(f"Blueprint:          MISSING (Run 'codsblu init' to create)")
        print("=" * 60)
        return 1

    content = blueprint.read_text(encoding="utf-8")
    is_distributed = sub_dir.is_dir() or "Sub-Blueprints Index" in content
    sub_count = len(list(sub_dir.glob("*.md"))) if sub_dir.is_dir() else 0

    # Parse metadata
    total_modules = 0
    v_ratio = "0%"
    health_status = "Unknown"
    last_updated = "Unknown"

    m_match = re.search(r"Total Tracked Modules\**\s*:\s*(\d+)", content)
    if m_match:
        total_modules = int(m_match.group(1))

    r_match = re.search(r"Verification Ratio\**\s*:\s*(\d+%)", content)
    if r_match:
        v_ratio = r_match.group(1)

    h_match = re.search(r"Health Status\**\s*:\s*([^\n\r]+)", content)
    if h_match:
        health_status = h_match.group(1).strip()

    u_match = re.search(r"Last Updated\**\s*:\s*([^\n\r]+)", content)
    if u_match:
        last_updated = u_match.group(1).strip()

    mode_label = f"Distributed ({sub_count} sub-blueprints)" if is_distributed else "Single-File"

    print(f"Architecture Mode:  {mode_label}")
    print(f"Blueprint File:     {blueprint}")
    print(f"Tracked Modules:    {total_modules}")
    print(f"Verification Ratio: {v_ratio} ({health_status})")
    print(f"Last Synchronized:  {last_updated}")
    print("-" * 60)

    # Check Watcher Status
    if watcher:
        pid_file = watcher.get_pid_file(root)
        if pid_file.is_file():
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
                if watcher.is_process_running(pid):
                    print(f"Background Watcher: RUNNING (PID: {pid})")
                else:
                    print("Background Watcher: STOPPED (Stale PID file)")
            except Exception:
                print("Background Watcher: STOPPED")
        else:
            print("Background Watcher: STOPPED (Run 'codsblu watch' to start)")

        pending_file = watcher.get_pending_file(root)
        if pending_file.is_file():
            try:
                with open(pending_file, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
                    print(f"Pending File Queue: {p_data.get('pending_count', 0)} files waiting for agent sync")
            except Exception:
                pass

    print("=" * 60)
    return 0


# ------------------------------------------------------------------------------
# Command: validate
# ------------------------------------------------------------------------------
def cmd_validate(args):
    import subprocess
    root = resolve_project_root(args.path)
    blueprint = get_blueprint_path(root) if not args.target else Path(args.target)

    val_script = CURRENT_DIR / "validate-blueprint.py"
    if not val_script.is_file():
        print("[ERR] validate-blueprint.py not found.", file=sys.stderr)
        return 1

    cmd = [sys.executable, str(val_script), "--path", str(blueprint)]
    if args.strict:
        cmd.append("--strict")
    if args.check_files:
        cmd.append("--check-files")
    if args.check_staleness:
        cmd.append("--check-staleness")
    if args.format:
        cmd.extend(["--format", args.format])

    res = subprocess.run(cmd)
    return res.returncode


# ------------------------------------------------------------------------------
# Command: migrate --to-distributed
# ------------------------------------------------------------------------------
def cmd_migrate(args):
    root = resolve_project_root(args.path)
    blueprint = get_blueprint_path(root)
    sub_dir = get_sub_blueprints_dir(root)

    if not blueprint.is_file():
        print(f"[ERR] No blueprint found at '{blueprint}' to migrate.", file=sys.stderr)
        return 1

    content = blueprint.read_text(encoding="utf-8")
    if "Sub-Blueprints Index" in content:
        print("[INFO] Blueprint is already in distributed mode.")
        return 0

    sub_dir.mkdir(parents=True, exist_ok=True)

    # Extract module rows from Section 5
    m_section = re.search(r"## 5\. Module Registry(.*?)(?=## 6\.)", content, re.DOTALL)
    if not m_section:
        print("[ERR] Could not locate Section 5 (Module Registry).", file=sys.stderr)
        return 1

    section_body = m_section.group(1).strip()
    table_lines = [l.strip() for l in section_body.splitlines() if l.strip().startswith("|")]

    domain_buckets = {}
    if len(table_lines) >= 3:
        for row in table_lines[2:]:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if len(cols) >= 5:
                mod_name = cols[0].strip("`'\" ")
                mod_path = cols[1].strip("`'\" ")
                mod_resp = cols[2]
                mod_deps = cols[3]
                mod_stat = cols[4]

                # Identify domain from path (e.g. src/modules/auth -> auth, or apps/api -> api)
                parts = Path(mod_path).parts
                domain = "core"
                if len(parts) >= 2 and parts[0] in ("src", "app", "apps", "packages", "lib"):
                    domain = parts[1] if parts[0] in ("apps", "packages") or len(parts) == 2 else parts[2]
                domain = re.sub(r"[^a-zA-Z0-9_-]", "", domain.lower())

                if domain not in domain_buckets:
                    domain_buckets[domain] = []
                domain_buckets[domain].append({
                    "name": mod_name,
                    "path": mod_path,
                    "responsibility": mod_resp,
                    "dependencies": mod_deps,
                    "status": mod_stat
                })

    # Generate sub-blueprints
    sub_index_rows = []
    for domain, mods in domain_buckets.items():
        sub_file = sub_dir / f"{domain}.md"
        mod_table_lines = [
            "| Sub-Module | Path | Responsibility | Internal Dependencies | Status |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        for m in mods:
            mod_table_lines.append(f"| `{m['name']}` | `{m['path']}` | {m['responsibility']} | {m['dependencies']} | {m['status']} |")

        sub_content = f"""# Domain Blueprint: {domain.capitalize()}

> Parent Index: `../codebase-map.md`
> Maintained by **Codsblu (blublu)**.

---

## 1. Domain Overview
- **Domain Identifier**: `{domain}`
- **Root Directory**: `src/modules/{domain}`
- **Primary Responsibility**: Domain slice handling {domain} business logic.
- **Domain Dependencies**: `Core`

---

## 2. Domain Entry Points & Exported Contracts
| Interface / Entry Point | File Path | Type | Consumers / Contract |
| :--- | :--- | :--- | :--- |

---

## 3. Domain Module Registry
{chr(10).join(mod_table_lines)}

---

## 4. Domain Data Flows

---

## 5. Domain Database Mapping
*N/A*

---

## 6. Domain Business Invariants

---

## 7. Domain Mapping Health
- **Last Updated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
- **Health Status**: Healthy
- **Verification Ratio**: 100%
"""
        sub_file.write_text(sub_content, encoding="utf-8")
        sub_index_rows.append(f"| `{domain.capitalize()}` | `.agents/sub-blueprints/{domain}.md` | `src/modules/{domain}` | [Verified] |")
        print(f"  [+] Created sub-blueprint: {sub_file.relative_to(root)}")

    # Update root blueprint with Sub-Blueprints Index
    if not sub_index_rows:
        sub_index_rows.append("| `Core` | `.agents/sub-blueprints/core.md` | `src/` | [Verified] |")

    sub_index_block = f"""
### Sub-Blueprints Index (Distributed Mode)
| Domain / Service | Sub-Blueprint Path | Scope / Root Path | Status |
| :--- | :--- | :--- | :--- |
{chr(10).join(sub_index_rows)}
"""
    new_content = content.replace("## 6. Dependency Mapping", sub_index_block + "\n---\n\n## 6. Dependency Mapping")
    blueprint.write_text(new_content, encoding="utf-8")
    print("✔ Successfully migrated blueprint to Distributed Mode.")
    return 0


# ------------------------------------------------------------------------------
# Command: watch
# ------------------------------------------------------------------------------
def cmd_watch(args):
    root = resolve_project_root(args.path)
    if not watcher:
        print("[ERR] watcher.py module not found.", file=sys.stderr)
        return 1

    watcher.start_watcher(root, debounce_ms=args.debounce)
    return 0


# ------------------------------------------------------------------------------
# Command: stop
# ------------------------------------------------------------------------------
def cmd_stop(args):
    root = resolve_project_root(args.path)
    if not watcher:
        print("[ERR] watcher.py module not found.", file=sys.stderr)
        return 1

    stopped = watcher.stop_watcher(root)
    if stopped:
        print("✔ Codsblu background watcher stopped.")
    else:
        print("No active watcher process was running.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="codsblu",
        description="Codsblu v1.2.0 — AI Codebase Memory & Architecture Tracking CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize codebase architecture blueprint")
    p_init.add_argument("--path", default=".", help="Project directory")
    p_init.add_argument("--distributed", action="store_true", help="Initialize in distributed mode (.agents/sub-blueprints/)")
    p_init.add_argument("--force", action="store_true", help="Force overwrite existing blueprint")

    # status
    p_status = subparsers.add_parser("status", help="Display architectural health summary")
    p_status.add_argument("--path", default=".", help="Project directory")

    # validate
    p_val = subparsers.add_parser("validate", help="Validate blueprint and sub-blueprints")
    p_val.add_argument("--path", default=".", help="Project directory")
    p_val.add_argument("--target", default="", help="Explicit target blueprint file")
    p_val.add_argument("--strict", action="store_true", help="Strict compliance checks")
    p_val.add_argument("--check-files", action="store_true", help="Verify filesystem paths")
    p_val.add_argument("--check-staleness", action="store_true", help="Detect modified unmapped files")
    p_val.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # migrate
    p_mig = subparsers.add_parser("migrate", help="Migrate single-file blueprint to distributed mode")
    p_mig.add_argument("--to-distributed", action="store_true", required=True, help="Migrate to distributed architecture")
    p_mig.add_argument("--path", default=".", help="Project directory")

    # watch
    p_watch = subparsers.add_parser("watch", help="Start local filesystem change watcher")
    p_watch.add_argument("--path", default=".", help="Project directory")
    p_watch.add_argument("--debounce", type=int, default=2000, help="Debounce delay in ms")

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop background file watcher")
    p_stop.add_argument("--path", default=".", help="Project directory")

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    handlers = {
        "init": cmd_init,
        "status": cmd_status,
        "validate": cmd_validate,
        "migrate": cmd_migrate,
        "watch": cmd_watch,
        "stop": cmd_stop,
    }

    code = handlers[args.subcommand](args)
    sys.exit(code or 0)


if __name__ == "__main__":
    main()
