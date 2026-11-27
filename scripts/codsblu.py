#!/usr/bin/env python3
"""
Codsblu (blublu) v2.0.0 — Unified CLI Engine
Autonomous codebase memory management, validation, status reporting, migration,
drift detection, dependency analysis, module inspection, and filesystem watcher.

New in v2.0.0:
  codsblu drift      -- Classify architecture drift per module (4 categories)
  codsblu analyze    -- Show hierarchical context for a specific module (L1→L3)
  codsblu dependencies -- Display dependency map for a module or entire project
  codsblu watch --scope <domain> -- Domain-scoped filesystem monitoring

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

    scope = getattr(args, "scope", None)
    watcher.start_watcher(root, debounce_ms=args.debounce, scope=scope)
    return 0


# ------------------------------------------------------------------------------
# Command: stop
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# Command: drift (v2.0.0)
# ------------------------------------------------------------------------------
def cmd_drift(args):
    """Run the architecture drift detection engine manually."""
    root = resolve_project_root(args.path)
    blueprint = get_blueprint_path(root)

    if not blueprint.is_file():
        print(f"[ERR] Blueprint not found: {blueprint}", file=sys.stderr)
        return 1

    # Import validate-blueprint's check_drift function dynamically
    validate_script = CURRENT_DIR / "validate-blueprint.py"
    check_drift_fn = None
    if validate_script.is_file():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("validate_blueprint", validate_script)
            vb_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(vb_mod)
            check_drift_fn = getattr(vb_mod, "check_drift", None)
            _print_drift_report = getattr(vb_mod, "_print_drift_report", None)
        except Exception as e:
            print(f"[WARN] Could not import validate-blueprint: {e}", file=sys.stderr)

    if check_drift_fn is None:
        # Fallback: delegate to subprocess
        import subprocess
        cmd = [
            sys.executable,
            str(validate_script),
            "--path", str(blueprint),
            "--check-drift",
        ]
        if hasattr(args, "exceptions") and args.exceptions:
            cmd += ["--drift-exceptions", args.exceptions]
        fmt = getattr(args, "format", "text")
        if fmt:
            cmd += ["--format", fmt]
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode

    # Parse module registry from blueprint
    content = blueprint.read_text(encoding="utf-8")
    sec5_match = re.search(r"##\s+5\.[^\n]*\n(.*?)(?=\n##\s+6\.|\Z)", content, re.DOTALL)
    module_registry = []
    if sec5_match:
        body = sec5_match.group(1)
        split = re.split(r"\n###", body)
        body = split[0] if split else body
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            if re.match(r"^\|[\s\-:| ]+\|$", stripped):
                continue
            cols = [c.strip() for c in stripped.split("|") if c.strip()]
            if len(cols) >= 2:
                name = cols[0].strip("`*").strip()
                path = cols[1].strip("`").strip()
                status = cols[-1] if len(cols) >= 3 else "[Unverified]"
                if name and name.lower() not in ("module", "domain", "service", "name"):
                    module_registry.append({"name": name, "path": path, "status": status})

    exceptions_str = getattr(args, "exceptions", "") or ""
    drift_result = check_drift_fn(str(blueprint), module_registry, exceptions_str)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(json.dumps(drift_result, indent=2))
    else:
        # Print drift report
        report = drift_result["drift_report"]
        summary = drift_result["summary"]
        print("=" * 60)
        print(" Architecture Drift Report (Codsblu v2.0.0)")
        print("=" * 60)
        print(f"Confirmed Drift:          {summary['confirmed']}")
        print(f"Potential Drift:          {summary['potential']}")
        print(f"Unverified Modules:       {summary['unverified']}")
        print(f"User-Approved Exceptions: {summary['approved_exceptions']}")
        print("-" * 60)
        if not report:
            print("No drift detected. All verified modules are up to date.")
        else:
            for entry in report:
                cat = entry["category"]
                icons = {
                    "Confirmed Drift": "[!!]",
                    "Potential Drift": "[??]",
                    "Unverified": "[ ]",
                    "User-Approved Exception": "[ok]",
                }
                icon = icons.get(cat, "[?]")
                print(f"\n{icon} [{cat}] {entry['module']}")
                print(f"     Path: {entry['path']}")
                if entry.get("changed_files"):
                    print(f"     Changed: {', '.join(entry['changed_files'][:3])}")
                print(f"     Recommendation: {entry['recommendation']}")
        print("=" * 60)
        print("NOTE: Drift detection is READ-ONLY. No blueprint changes were made.")
    return 0


# ------------------------------------------------------------------------------
# Command: analyze (v2.0.0)
# ------------------------------------------------------------------------------
def cmd_analyze(args):
    """Display hierarchical architecture context for a specific module (L1 → L3)."""
    root = resolve_project_root(args.path)
    blueprint = get_blueprint_path(root)
    module_name = getattr(args, "module_name", "").strip()

    if not module_name:
        print("[ERR] Please provide a module name: codsblu analyze <module-name>", file=sys.stderr)
        return 1

    if not blueprint.is_file():
        print(f"[ERR] Blueprint not found: {blueprint}", file=sys.stderr)
        return 1

    print("=" * 60)
    print(f" Module Analysis: {module_name}")
    print("=" * 60)

    # Level 1: Search in root blueprint
    content = blueprint.read_text(encoding="utf-8")
    sec5_match = re.search(r"##\s+5\.[^\n]*\n(.*?)(?=\n##\s+6\.|\Z)", content, re.DOTALL)
    l1_entry = None
    domain_hint = None

    if sec5_match:
        body = sec5_match.group(1).split("###")[0]
        for line in body.splitlines():
            if not line.strip().startswith("|"):
                continue
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) >= 2:
                name = cols[0].strip("`*").strip()
                if name.lower() == module_name.lower() or module_name.lower() in name.lower():
                    l1_entry = cols
                    domain_hint = name
                    break

    if l1_entry:
        print(f"\n[Level 1] Found in root blueprint:")
        print(f"  Module: {l1_entry[0]}")
        print(f"  Path:   {l1_entry[1] if len(l1_entry) > 1 else 'N/A'}")
        print(f"  Status: {l1_entry[-1] if len(l1_entry) >= 3 else 'N/A'}")
    else:
        print(f"\n[Level 1] '{module_name}' not found in root blueprint Module Registry.")
        print(f"  → Load .agents/codebase-map.md for full global context.")

    # Level 2: Search in sub-blueprints
    sub_dir = get_sub_blueprints_dir(root)
    l2_file = None
    l2_entry = None

    if sub_dir.is_dir():
        # Look for a sub-blueprint whose name or content mentions the module
        for md_file in sorted(sub_dir.glob("*.md")):
            sub_content = md_file.read_text(encoding="utf-8")
            if module_name.lower() in sub_content.lower():
                l2_file = md_file
                # Try to extract the specific row
                for line in sub_content.splitlines():
                    if not line.strip().startswith("|"):
                        continue
                    cols = [c.strip() for c in line.split("|") if c.strip()]
                    if len(cols) >= 2:
                        name = cols[0].strip("`*").strip()
                        if name.lower() == module_name.lower():
                            l2_entry = cols
                            break
                break

        if l2_file:
            print(f"\n[Level 2] Found in domain sub-blueprint: {l2_file.name}")
            if l2_entry:
                print(f"  Module: {l2_entry[0]}")
                print(f"  Path:   {l2_entry[1] if len(l2_entry) > 1 else 'N/A'}")
                print(f"  Responsibility: {l2_entry[2] if len(l2_entry) > 2 else 'N/A'}")
                print(f"  Status: {l2_entry[-1] if len(l2_entry) >= 3 else 'N/A'}")
            print(f"  → Full domain context: {l2_file.relative_to(root)}")
        else:
            print(f"\n[Level 2] '{module_name}' not found in any domain sub-blueprint.")
            print(f"  → No Level 2 file exists yet. Use 'codsblu migrate --to-distributed' to create them.")

    # Level 3: Check for module-level blueprint
    l3_found = False
    if sub_dir.is_dir():
        for md_file in sorted(sub_dir.rglob("*.md")):
            if md_file.parent == sub_dir:
                continue  # Skip Level 2 files (direct children)
            stem = md_file.stem.lower().replace("-", "_").replace(" ", "_")
            if stem == module_name.lower().replace("-", "_").replace(" ", "_") or module_name.lower() in stem:
                l3_found = True
                print(f"\n[Level 3] Module blueprint found: {md_file.relative_to(root)}")
                # Print first few lines of the Level 3 file
                l3_lines = md_file.read_text(encoding="utf-8").splitlines()[:15]
                for ln in l3_lines:
                    if ln.strip():
                        print(f"  {ln}")
                print(f"  → Load this file for public interface and DB entity details.")
                break

    if not l3_found:
        print(f"\n[Level 3] No module-level blueprint found for '{module_name}'.")
        print(f"  → Level 3 is optional. Create .agents/sub-blueprints/<domain>/{module_name.lower()}.md if needed.")

    print(f"\n[Level 4] Load only on explicit user request for implementation details.")
    print("=" * 60)
    return 0


# ------------------------------------------------------------------------------
# Command: dependencies (v2.0.0)
# ------------------------------------------------------------------------------
def cmd_dependencies(args):
    """Display the dependency map extracted from blueprint Mermaid graphs and tables."""
    root = resolve_project_root(args.path)
    blueprint = get_blueprint_path(root)
    filter_module = getattr(args, "module", "") or ""
    fmt = getattr(args, "format", "table")

    if not blueprint.is_file():
        print(f"[ERR] Blueprint not found: {blueprint}", file=sys.stderr)
        return 1

    all_edges = []

    def parse_edges_from_content(content, source_file="root"):
        edges = []
        # Parse Mermaid graphs
        mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)```", content, re.DOTALL)
        for block in mermaid_blocks:
            for line in block.splitlines():
                line = line.strip()
                # Match: NodeA --> NodeB, NodeA -.-> NodeB, NodeA -->|label| NodeB
                m = re.match(
                    r'(\w+)(?:\[.*?\]|\(\(.*?\)\))?\s*(-->|-.->|==>)(?:\|([^|]+)\|)?\s*(\w+)',
                    line
                )
                if m:
                    src, arrow, label, tgt = m.groups()
                    etype = "event" if "-.->" in arrow else ("import" if "-->" in arrow else "api")
                    edges.append({
                        "source": src, "target": tgt, "type": etype,
                        "label": label.strip() if label else f"{src}→{tgt}",
                        "confidence": "Inferred",
                        "source_file": source_file,
                    })

        # Parse dependency tables
        table_pattern = re.compile(
            r"\|[^\n]*\bSource\b[^\n]*\|\n\|[-: |]+\|\n((?:\|[^\n]+\|\n?)+)",
            re.IGNORECASE
        )
        for match in table_pattern.finditer(content):
            for line in match.group(1).strip().splitlines():
                cols = [c.strip() for c in line.split("|") if c.strip()]
                if len(cols) >= 4:
                    src = cols[0].strip("`*").strip()
                    tgt = cols[1].strip("`*").strip()
                    etype = cols[2].strip().lower()
                    label = cols[3] if len(cols) > 3 else ""
                    conf_raw = cols[-1] if len(cols) >= 5 else "Inferred"
                    conf = ("Confirmed" if "confirmed" in conf_raw.lower()
                            else "Unverified" if "unverified" in conf_raw.lower()
                            else "Inferred")
                    if src and tgt and src.lower() not in ("source", "module"):
                        edges.append({
                            "source": src, "target": tgt, "type": etype,
                            "label": label, "confidence": conf,
                            "source_file": source_file,
                        })
        return edges

    # Parse root blueprint
    content = blueprint.read_text(encoding="utf-8")
    all_edges += parse_edges_from_content(content, "codebase-map.md")

    # Parse sub-blueprints
    sub_dir = get_sub_blueprints_dir(root)
    if sub_dir.is_dir():
        for md_file in sorted(sub_dir.rglob("*.md")):
            sub_content = md_file.read_text(encoding="utf-8")
            all_edges += parse_edges_from_content(sub_content, md_file.name)

    # Deduplicate
    seen = set()
    unique_edges = []
    for e in all_edges:
        key = (e["source"], e["target"], e["type"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    # Filter by module if requested
    if filter_module:
        fname = filter_module.lower()
        unique_edges = [
            e for e in unique_edges
            if fname in e["source"].lower() or fname in e["target"].lower()
        ]

    if not unique_edges:
        scope_msg = f" for module '{filter_module}'" if filter_module else ""
        print(f"No dependencies found{scope_msg}.")
        return 0

    if fmt == "json":
        print(json.dumps(unique_edges, indent=2))
    else:
        # Markdown table format
        header = "| Source | Target | Type | Label | Confidence |"
        sep = "| :--- | :--- | :--- | :--- | :--- |"
        print(header)
        print(sep)
        for e in unique_edges:
            print(f"| `{e['source']}` | `{e['target']}` | `{e['type']}` | {e['label']} | {e['confidence']} |")

    print(f"\n[INFO] Total edges: {len(unique_edges)}", file=sys.stderr)
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="codsblu",
        description="Codsblu v2.0.0 — AI Codebase Memory & Architecture Tracking CLI",
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

    # watch (enhanced in v2.0.0 with --scope)
    p_watch = subparsers.add_parser("watch", help="Start local filesystem change watcher")
    p_watch.add_argument("--path", default=".", help="Project directory")
    p_watch.add_argument("--debounce", type=int, default=2000, help="Debounce delay in ms")
    p_watch.add_argument("--scope", default="", help="Watch only a specific domain directory (e.g. 'order')")

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop background file watcher")
    p_stop.add_argument("--path", default=".", help="Project directory")

    # drift (v2.0.0)
    p_drift = subparsers.add_parser("drift", help="Run architecture drift detection engine")
    p_drift.add_argument("--path", default=".", help="Project directory")
    p_drift.add_argument("--exceptions", default="", help="Comma-separated module names to mark as user-approved exceptions")
    p_drift.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # analyze (v2.0.0)
    p_analyze = subparsers.add_parser("analyze", help="Show hierarchical architecture context for a module (L1→L3)")
    p_analyze.add_argument("module_name", help="Module name or path to analyze")
    p_analyze.add_argument("--path", default=".", help="Project directory")

    # dependencies (v2.0.0)
    p_deps = subparsers.add_parser("dependencies", help="Display dependency map for a module or entire project")
    p_deps.add_argument("--path", default=".", help="Project directory")
    p_deps.add_argument("--module", default="", help="Filter to edges involving this module name")
    p_deps.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

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
        "drift": cmd_drift,
        "analyze": cmd_analyze,
        "dependencies": cmd_dependencies,
    }

    code = handlers[args.subcommand](args)
    sys.exit(code or 0)


if __name__ == "__main__":
    main()
