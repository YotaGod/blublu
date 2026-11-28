#!/usr/bin/env python3
"""
blublu v2.0.0 — Architectural Blueprint Validator
Validates structural integrity, section coverage, module registry consistency,
Mermaid diagram syntax, filesystem references, staleness detection, and
architecture drift classification (Confirmed / Potential / Unverified / User-Approved).

New in v2.0.0:
  --check-drift       : Classify per-module architecture drift (4 categories)
  --drift-exceptions  : Comma-separated modules exempt from drift reporting
  --validate-graph    : Validate a graph_export.py JSON output file

Dependencies: Pure Python 3 standard library (no pip packages required).
"""

import sys
import os
import re
import argparse
import json
from pathlib import Path

# Add scripts directory to sys.path to import scanner module
CURRENT_SCRIPT_DIR = Path(__file__).resolve().parent
if str(CURRENT_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_SCRIPT_DIR))

try:
    import scanner
except ImportError:
    scanner = None


EXPECTED_SECTIONS = [
    (1, "Project Overview"),
    (2, "Entry Points"),
    (3, "Directory Structure"),
    (4, "Architecture Overview"),
    (5, "Module Registry"),
    (6, "Dependency Mapping"),
    (7, "Main Data Flows"),
    (8, "API Mapping"),
    (9, "Database Mapping"),
    (10, "External Integrations"),
    (11, "Project Conventions"),
    (12, "Important Business Rules"),
    (13, "Known Limitations & Technical Debt"),
    (14, "Recent Architectural Changes"),
    (15, "Mapping Health"),
]

VALID_STATUSES = {"[Verified]", "[Inferred]", "[Unverified]", "[Stale]"}

VALID_MERMAID_DECLARATIONS = {
    "graph",
    "flowchart",
    "sequencediagram",
    "classdiagram",
    "erdiagram",
    "statediagram",
    "statediagram-v2",
    "gitgraph",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate blublu architectural blueprints (.agents/codebase-map.md)."
    )
    parser.add_argument(
        "--path",
        default=".agents/codebase-map.md",
        help="Path to the blueprint file (default: .agents/codebase-map.md)",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Verify that paths referenced in tables exist on the filesystem",
    )
    parser.add_argument(
        "--check-staleness",
        action="store_true",
        help="Detect modified source files not reflected in blueprint (Architecture Drift)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: 'text' (default) or 'json'",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any missing optional sections, unverified statuses, stale modules, or invalid Mermaid syntax",
    )
    parser.add_argument(
        "--check-drift",
        action="store_true",
        help="Classify architecture drift per module: Confirmed / Potential / Unverified / User-Approved Exception",
    )
    parser.add_argument(
        "--drift-exceptions",
        default="",
        help="Comma-separated module names marked as user-approved drift exceptions",
    )
    parser.add_argument(
        "--validate-graph",
        default="",
        metavar="FILE",
        help="Validate a graph_export.py JSON output file for blublu v2.0.0 schema compliance",
    )
    return parser.parse_args()


def extract_sections(content):
    """
    Extracts all level-2 markdown headings (## [Number]. [Title]) and their contents.
    """
    pattern = re.compile(r"^##\s+(\d+)\.\s+([^\n\r]+)", re.MULTILINE)
    matches = list(pattern.finditer(content))
    sections = {}

    for i, match in enumerate(matches):
        sec_num = int(match.group(1))
        sec_title = match.group(2).strip()
        start_idx = match.end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sec_body = content[start_idx:end_idx].strip()
        sections[sec_num] = {
            "title": sec_title,
            "body": sec_body,
            "raw_match": match.group(0),
        }

    return sections


def parse_module_registry(body):
    """
    Parses Section 5 (Module Registry) Markdown table.
    Expected columns: Module, Path, Responsibility, Dependencies, Status.
    Stops before any sub-heading (such as ### Sub-Blueprints Index).
    """
    # Isolate primary Module Registry table from any subsequent sub-tables
    primary_part = body.split("###")[0]
    lines = [line.strip() for line in primary_part.splitlines() if line.strip()]
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]

    if len(table_lines) < 2:
        return None, ["Module Registry does not contain a valid Markdown table."]

    headers = [col.strip().lower() for col in table_lines[0].split("|")[1:-1]]
    expected_cols = ["module", "path", "responsibility", "dependencies", "status"]

    missing_cols = [c for c in expected_cols if c not in headers]
    if missing_cols:
        return None, [f"Module Registry missing expected column(s): {', '.join(missing_cols)}"]

    col_indices = {col: headers.index(col) for col in expected_cols}
    modules = []
    errors = []

    data_rows = table_lines[2:]

    for line_num, row_str in enumerate(data_rows, start=3):
        cols = [c.strip() for c in row_str.split("|")[1:-1]]
        if len(cols) < len(headers):
            errors.append(f"Row {line_num} has fewer columns ({len(cols)}) than headers ({len(headers)}).")
            continue

        raw_module = cols[col_indices["module"]]
        raw_path = cols[col_indices["path"]]
        raw_resp = cols[col_indices["responsibility"]]
        raw_deps = cols[col_indices["dependencies"]]
        raw_status = cols[col_indices["status"]]

        clean_path = raw_path.strip("`'\" \t")
        clean_module = raw_module.strip("`'\" \t")
        clean_status = raw_status.strip()

        if clean_status not in VALID_STATUSES:
            matched_status = None
            for s in VALID_STATUSES:
                if s.lower() in clean_status.lower():
                    matched_status = s
                    break
            if matched_status:
                clean_status = matched_status
            else:
                errors.append(f"Row {line_num} (`{clean_module}`): Invalid status tag '{raw_status}'. Must be one of {VALID_STATUSES}.")

        modules.append({
            "name": clean_module,
            "path": clean_path,
            "responsibility": raw_resp,
            "dependencies": raw_deps,
            "status": clean_status,
        })

    return modules, errors


def validate_mermaid_blocks(content: str) -> tuple:
    """
    Extracts and validates Mermaid code blocks.
    Detects missing declarations, unclosed brackets, malformed arrows, and unquoted labels.
    Provides graceful Markdown table fallback if syntax is defective.
    """
    pattern = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
    matches = list(pattern.finditer(content))
    errors = []
    warnings = []
    fallback_tables = []

    for block_idx, match in enumerate(matches, start=1):
        block_text = match.group(1).strip()
        lines = [line.strip() for line in block_text.splitlines() if line.strip()]

        if not lines:
            errors.append(f"Mermaid Block #{block_idx}: Empty diagram block.")
            continue

        # 1. Validate declaration
        header_tokens = lines[0].split()
        first_token = header_tokens[0].lower() if header_tokens else ""
        if first_token not in VALID_MERMAID_DECLARATIONS:
            errors.append(
                f"Mermaid Block #{block_idx}: Invalid declaration '{lines[0]}'. "
                f"Must start with one of: {', '.join(sorted(VALID_MERMAID_DECLARATIONS))}."
            )

        # Track parsed relationships for fallback table
        parsed_relations = []

        # 2. Line by line validation
        for line_num, line in enumerate(lines[1:], start=2):
            # Skip comments
            if line.startswith("%%"):
                continue

            # Bracket balancing
            if line.count("[") != line.count("]"):
                errors.append(f"Mermaid Block #{block_idx}, Line {line_num}: Unbalanced square brackets `[` `]` in: '{line}'")
            if line.count("(") != line.count(")"):
                errors.append(f"Mermaid Block #{block_idx}, Line {line_num}: Unbalanced parentheses `(` `)` in: '{line}'")
            if line.count("{") != line.count("}"):
                errors.append(f"Mermaid Block #{block_idx}, Line {line_num}: Unbalanced curly braces `{{` `}}` in: '{line}'")

            # Check for unquoted node labels with slashes or spaces
            # Pattern: Node[path/or with space] without quotes
            unquoted_match = re.search(r'\b[a-zA-Z0-9_-]+\[([^"\]\n]*[ /\\:][^"\]\n]*)\]', line)
            if unquoted_match:
                errors.append(
                    f"Mermaid Block #{block_idx}, Line {line_num}: Label '{unquoted_match.group(1)}' "
                    f"contains paths/spaces but lacks double quotes. Use [\"...\"] syntax."
                )

            # Check for malformed single dash arrows e.g. -> instead of --> in flowchart
            if first_token in ("graph", "flowchart"):
                # Matches single arrow -> but not --> or -.-> or ==>
                if re.search(r'(?<!-)(?<!\.)->(?![>])', line):
                    errors.append(
                        f"Mermaid Block #{block_idx}, Line {line_num}: Malformed arrow `->`. "
                        f"Flowcharts require `-->`, `-.->`, or `==>`."
                    )

            # Extract relationship candidate for fallback table
            arrow_match = re.search(r'([a-zA-Z0-9_\-\.\/\"\'\s]+?)\s*(-->|-\.->|==>|->)\s*([a-zA-Z0-9_\-\.\/\"\'\(\)\{\}\s]+)', line)
            if arrow_match:
                src = arrow_match.group(1).strip().strip('"')
                rel = arrow_match.group(2).strip()
                dst = arrow_match.group(3).strip().strip('"')
                # Clean node definitions e.g. Node["Label"] -> Label
                src_clean = re.sub(r'^[a-zA-Z0-9_-]+\["?(.*?)"?\]$', r'\1', src)
                dst_clean = re.sub(r'^[a-zA-Z0-9_-]+\["?(.*?)"?\]$', r'\1', dst)
                parsed_relations.append((src_clean, dst_clean, rel))

        # If errors were found and we extracted relations, construct fallback Markdown table
        if errors and parsed_relations:
            fb_lines = [
                f"\n### Fallback Relationship Table for Mermaid Block #{block_idx}:",
                "| Source Module | Target Module | Relationship |",
                "| :--- | :--- | :--- |"
            ]
            for s, d, r in parsed_relations:
                rel_desc = "Dependency" if "-->" in r else ("Optional / Event" if "-.->" in r else "Critical Path")
                fb_lines.append(f"| `{s}` | `{d}` | {rel_desc} (`{r}`) |")
            fallback_tables.append("\n".join(fb_lines))

    return errors, warnings, fallback_tables


def parse_mapping_health(body):
    """
    Parses Section 15 (Mapping Health) for metadata and declared ratio.
    """
    health = {
        "last_updated": None,
        "health_status": None,
        "declared_ratio": None,
        "total_modules": None,
    }

    date_match = re.search(r"Last Updated\**\s*:\s*([^\n\r]+)", body, re.IGNORECASE)
    if date_match:
        health["last_updated"] = date_match.group(1).strip()

    status_match = re.search(r"Health Status\**\s*:\s*([^\n\r]+)", body, re.IGNORECASE)
    if status_match:
        health["health_status"] = status_match.group(1).strip()

    ratio_match = re.search(r"Verification Ratio\**\s*:\s*(\d+)%", body, re.IGNORECASE)
    if ratio_match:
        health["declared_ratio"] = int(ratio_match.group(1))

    total_match = re.search(r"Total Tracked Modules\**\s*:\s*(\d+)", body, re.IGNORECASE)
    if total_match:
        health["total_modules"] = int(total_match.group(1))

    return health


def check_staleness(project_root: Path, modules: list) -> list:
    """
    Detects modules whose source files were modified on disk without blueprint synchronization.
    Uses Git diff if available, or filesystem cache scanner as fallback.
    """
    if not scanner:
        return []

    scan_res = scanner.scan_changes(str(project_root), save_cache=False)
    all_changed = set(scan_res.get("all_changed", []))
    stale_modules = []

    for mod in modules:
        mod_path = mod["path"].strip("/\\").replace("\\", "/")
        if not mod_path or mod_path == "N/A":
            continue

        # Check if any changed file starts with module path
        matching_changes = [
            f for f in all_changed
            if f == mod_path or f.startswith(mod_path + "/")
        ]

        if matching_changes:
            stale_modules.append({
                "module": mod["name"],
                "path": mod["path"],
                "status": mod["status"],
                "changed_files": matching_changes,
            })

    return stale_modules


def validate_sub_blueprints(project_root: Path, root_content: str, check_files: bool = False, strict: bool = False) -> dict:
    """
    Validates distributed architecture sub-blueprints (.agents/sub-blueprints/*.md).
    Checks existence of registered sub-blueprints, syntax integrity, and flags orphaned files.
    """
    sub_dir = project_root / ".agents" / "sub-blueprints"
    res = {
        "is_distributed": False,
        "registered": [],
        "missing": [],
        "orphaned": [],
        "errors": [],
        "warnings": [],
    }

    # Extract sub-blueprint table rows
    idx_match = re.search(r"### Sub-Blueprints Index[^\n]*\n(.*?)(?=\n## |\Z)", root_content, re.DOTALL)
    registered_files = set()

    if idx_match:
        res["is_distributed"] = True
        t_lines = [l.strip() for l in idx_match.group(1).splitlines() if l.strip().startswith("|")]
        if len(t_lines) >= 3:
            for row in t_lines[2:]:
                cols = [c.strip() for c in row.split("|")[1:-1]]
                if len(cols) >= 2:
                    dom_name = cols[0].strip("`'\" ")
                    sub_rel = cols[1].strip("`'\" ")
                    if not sub_rel or sub_rel == "N/A":
                        continue

                    sub_full = project_root / sub_rel
                    registered_files.add(sub_full.resolve())
                    res["registered"].append({
                        "domain": dom_name,
                        "path": sub_rel,
                        "exists": sub_full.is_file(),
                    })

                    if not sub_full.is_file():
                        res["missing"].append(sub_rel)
                        res["errors"].append(f"Registered sub-blueprint '{sub_rel}' does not exist on disk.")
                    else:
                        # Validate sub-blueprint content
                        try:
                            sub_text = sub_full.read_text(encoding="utf-8")
                            m_errs, _, _ = validate_mermaid_blocks(sub_text)
                            if m_errs:
                                res["errors"].extend([f"[{sub_rel}] {e}" for e in m_errs])
                        except Exception as exc:
                            res["errors"].append(f"Failed to read sub-blueprint '{sub_rel}': {exc}")

    # Check for orphaned sub-blueprints on disk
    if sub_dir.is_dir():
        for md_file in sub_dir.glob("*.md"):
            if md_file.resolve() not in registered_files:
                rel_path = f".agents/sub-blueprints/{md_file.name}"
                res["orphaned"].append(rel_path)
                msg = f"Orphaned sub-blueprint '{rel_path}' exists on disk but is not indexed in root blueprint."
                if strict:
                    res["errors"].append(msg)
                else:
                    res["warnings"].append(msg)

    return res


def validate_blueprint(file_path, check_files=False, check_staleness_flag=False, strict=False):
    target = Path(file_path)
    result = {
        "valid": False,
        "file": str(target),
        "errors": [],
        "warnings": [],
        "metrics": {
            "total_modules": 0,
            "verified": 0,
            "inferred": 0,
            "unverified": 0,
            "stale": 0,
            "verification_ratio": 0.0,
            "health_category": "Needs Rebuild",
        },
        "sections_found": [],
        "sections_missing": [],
        "broken_paths": [],
        "mermaid_errors": [],
        "mermaid_fallback_tables": [],
        "stale_modules": [],
    }

    # 1. File existence
    if not target.is_file():
        result["errors"].append(f"Blueprint file does not exist at '{target}'.")
        return result

    try:
        content = target.read_text(encoding="utf-8")
    except Exception as exc:
        result["errors"].append(f"Failed to read file: {exc}")
        return result

    if not content.strip():
        result["errors"].append("Blueprint file is empty.")
        return result

    # 2. Section coverage
    sections = extract_sections(content)
    result["sections_found"] = [s["title"] for s in sections.values()]

    for sec_num, sec_name in EXPECTED_SECTIONS:
        if sec_num not in sections:
            found = False
            for s_num, s_data in sections.items():
                if sec_name.lower() in s_data["title"].lower():
                    found = True
                    break
            if not found:
                result["sections_missing"].append(f"Section {sec_num}: {sec_name}")

    if result["sections_missing"]:
        msg = f"Missing {len(result['sections_missing'])} expected section(s): {', '.join(result['sections_missing'])}"
        if strict:
            result["errors"].append(msg)
        else:
            result["warnings"].append(msg)

    # 3. Mermaid Diagram Validation
    mermaid_errs, mermaid_warns, fb_tables = validate_mermaid_blocks(content)
    if mermaid_errs:
        result["mermaid_errors"].extend(mermaid_errs)
        result["errors"].extend(mermaid_errs)
    if mermaid_warns:
        result["warnings"].extend(mermaid_warns)
    if fb_tables:
        result["mermaid_fallback_tables"].extend(fb_tables)

    # 4. Module Registry check
    modules = []
    if 5 in sections:
        modules, reg_errors = parse_module_registry(sections[5]["body"])
        if reg_errors:
            result["errors"].extend(reg_errors)

        if modules:
            total = len(modules)
            v_count = sum(1 for m in modules if m["status"] == "[Verified]")
            i_count = sum(1 for m in modules if m["status"] == "[Inferred]")
            u_count = sum(1 for m in modules if m["status"] == "[Unverified]")
            s_count = sum(1 for m in modules if m["status"] == "[Stale]")

            ratio = (v_count / total * 100) if total > 0 else 0.0

            result["metrics"]["total_modules"] = total
            result["metrics"]["verified"] = v_count
            result["metrics"]["inferred"] = i_count
            result["metrics"]["unverified"] = u_count
            result["metrics"]["stale"] = s_count
            result["metrics"]["verification_ratio"] = round(ratio, 1)

            if ratio >= 90.0:
                result["metrics"]["health_category"] = "Healthy"
            elif ratio >= 70.0:
                result["metrics"]["health_category"] = "Drift Detected"
            else:
                result["metrics"]["health_category"] = "Needs Rebuild"

            project_root = target.parent.parent if target.parent.name == ".agents" else target.parent

            # 5. Filesystem path check
            if check_files:
                for mod in modules:
                    mod_path = mod["path"]
                    if mod_path.startswith("http://") or mod_path.startswith("https://") or mod_path == "N/A":
                        continue
                    full_path = project_root / mod_path
                    if not full_path.exists():
                        result["broken_paths"].append({
                            "module": mod["name"],
                            "path": mod_path,
                            "resolved": str(full_path),
                        })

            # 6. Staleness / Architecture Drift Detection
            if check_staleness_flag:
                stale_list = check_staleness(project_root, modules)
                if stale_list:
                    result["stale_modules"] = stale_list
                    for sm in stale_list:
                        msg = (
                            f"Module `{sm['module']}` ({sm['path']}) has modified source files "
                            f"({', '.join(sm['changed_files'][:3])}) but is tagged {sm['status']}."
                        )
                        if strict:
                            result["errors"].append(msg)
                        else:
                            result["warnings"].append(msg)

            # 7. Distributed Architecture Sub-Blueprints Validation
            sub_results = validate_sub_blueprints(project_root, content, check_files=check_files, strict=strict)
            result["distributed_mode"] = sub_results["is_distributed"]
            result["sub_blueprints"] = sub_results
            if sub_results["errors"]:
                result["errors"].extend(sub_results["errors"])
            if sub_results["warnings"]:
                result["warnings"].extend(sub_results["warnings"])
    else:
        result["errors"].append("Section 5 (Module Registry) is missing or unparseable.")

    if result["broken_paths"]:
        result["errors"].append(
            f"Found {len(result['broken_paths'])} broken path reference(s) on disk: " +
            ", ".join(f"`{b['path']}`" for b in result["broken_paths"])
        )

    # 7. Mapping Health integrity
    if 15 in sections:
        health_meta = parse_mapping_health(sections[15]["body"])
        if not health_meta["last_updated"]:
            result["warnings"].append("Section 15: Missing 'Last Updated' timestamp.")
        if health_meta["declared_ratio"] is not None and result["metrics"]["total_modules"] > 0:
            computed_int = int(round(result["metrics"]["verification_ratio"]))
            if abs(computed_int - health_meta["declared_ratio"]) > 5:
                diff_msg = f"Section 15 declared ratio ({health_meta['declared_ratio']}%) deviates from computed ratio ({computed_int}%)."
                if strict:
                    result["errors"].append(diff_msg)
                else:
                    result["warnings"].append(diff_msg)

    result["module_registry"] = modules
    result["valid"] = len(result["errors"]) == 0
    return result


# ---------------------------------------------------------------------------
# v2.0.0: Architecture Drift Detection Engine
# ---------------------------------------------------------------------------

def _get_changed_files_since(root: Path, since_date: str) -> list:
    """
    Returns list of files changed since since_date.
    Uses git diff if available, falls back to filesystem mtime comparison.
    """
    changed = []
    # Try git first
    try:
        import subprocess
        result = subprocess.run(
            ["git", "log", f"--since={since_date}", "--name-only", "--pretty=format:", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                line = line.strip()
                if line:
                    changed.append(line)
            return list(set(changed))
    except Exception:
        pass

    # Fallback: filesystem mtime comparison
    try:
        import datetime as dt_mod
        try:
            since_dt = dt_mod.datetime.fromisoformat(since_date.replace("Z", "+00:00"))
        except Exception:
            # Try YYYY-MM-DD format
            since_dt = dt_mod.datetime.strptime(since_date[:10], "%Y-%m-%d").replace(
                tzinfo=dt_mod.timezone.utc
            )
        since_ts = since_dt.timestamp()

        IGNORE_DIRS = {
            "node_modules", "vendor", ".git", "dist", "build", "out",
            "target", "coverage", ".cache", "__pycache__", ".agents",
        }
        for item in root.rglob("*"):
            if item.is_file():
                # Check if any parent dir is in ignore list
                parts = set(item.relative_to(root).parts)
                if parts & IGNORE_DIRS:
                    continue
                try:
                    if item.stat().st_mtime > since_ts:
                        changed.append(str(item.relative_to(root)))
                except OSError:
                    pass
    except Exception:
        pass

    return changed


def _has_structural_change(file_path: Path) -> bool:
    """
    Heuristic: check if a source file contains structural keywords
    that indicate architectural (interface/contract) changes.
    """
    STRUCTURAL_KEYWORDS = [
        "export ", "exports.", "module.exports", "export default",
        "export class", "export function", "export const",
        "def ", "class ", "async def ",  # Python
        "public ", "interface ", "abstract ",  # Java/C#/TS
        "func ", "type ",  # Go
        "CREATE TABLE", "ALTER TABLE", "DROP TABLE",  # SQL
        "@app.route", "@router.", "app.get(", "app.post(",  # Routes
        "addEventListener", "emit(", "on(",  # Events
    ]
    if not file_path.is_file():
        return False
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        for kw in STRUCTURAL_KEYWORDS:
            if kw in content:
                return True
    except Exception:
        pass
    return False


def check_drift(blueprint_path: str, module_registry: list, drift_exceptions_str: str) -> dict:
    """
    Classify architecture drift for each registered module.

    Categories:
      - Confirmed Drift: Module source files changed AND structural keywords detected.
      - Potential Drift: Module source files changed but no structural keywords.
      - Unverified: Module status is [Unverified] or [Stale] in registry.
      - User-Approved Exception: Module name in drift_exceptions_str.

    SAFETY: This function is READ-ONLY. It never modifies any blueprint file.
    """
    bp = Path(blueprint_path)
    if not bp.is_file():
        return {"drift_report": [], "summary": {
            "confirmed": 0, "potential": 0, "unverified": 0, "approved_exceptions": 0
        }}

    # Determine project root
    if bp.parent.name == ".agents":
        root = bp.parent.parent
    else:
        root = bp.parent

    # Read last_updated from Section 15
    content = bp.read_text(encoding="utf-8")
    health_match = re.search(
        r"##\s+15\.[^\n]*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
    )
    last_updated = ""
    if health_match:
        lu_match = re.search(r"\*\*Last Updated\*\*[:\s]+([^\n]+)", health_match.group(1))
        if lu_match:
            last_updated = lu_match.group(1).strip()

    # Get changed files since last_updated
    changed_files = []
    if last_updated:
        changed_files = _get_changed_files_since(root, last_updated)

    changed_set = set(changed_files)
    exceptions = {m.strip().lower() for m in drift_exceptions_str.split(",") if m.strip()}

    drift_report = []
    summary = {"confirmed": 0, "potential": 0, "unverified": 0, "approved_exceptions": 0}

    for module in module_registry:
        mod_name = module.get("name", "")
        mod_path = module.get("path", "")
        mod_status = module.get("status", "")
        mod_name_lower = mod_name.lower()

        # Category: User-Approved Exception
        if mod_name_lower in exceptions:
            drift_report.append({
                "module": mod_name,
                "path": mod_path,
                "category": "User-Approved Exception",
                "changed_files": [],
                "recommendation": "No action required — explicitly approved by user.",
            })
            summary["approved_exceptions"] += 1
            continue

        # Category: Unverified (never verified against source)
        if mod_status in ("[Unverified]", "Unverified", "[Stale]", "Stale"):
            drift_report.append({
                "module": mod_name,
                "path": mod_path,
                "category": "Unverified",
                "changed_files": [],
                "recommendation": f"Inspect source at '{mod_path}' and elevate status to [Verified].",
            })
            summary["unverified"] += 1
            continue

        # Find changed files matching this module's path prefix
        mod_path_norm = mod_path.lstrip("./").replace("\\", "/")
        module_changed = [
            f for f in changed_set
            if f.replace("\\", "/").startswith(mod_path_norm) or mod_path_norm in f.replace("\\", "/")
        ]

        if not module_changed:
            # No drift detected for this module
            continue

        # Check for structural changes in changed files
        has_structural = False
        for rel_path in module_changed:
            abs_path = root / rel_path
            if _has_structural_change(abs_path):
                has_structural = True
                break

        if has_structural:
            drift_report.append({
                "module": mod_name,
                "path": mod_path,
                "category": "Confirmed Drift",
                "changed_files": module_changed[:5],
                "recommendation": f"Update blueprint for '{mod_name}' — structural/interface changes detected. Run: blublu update",
            })
            summary["confirmed"] += 1
        else:
            drift_report.append({
                "module": mod_name,
                "path": mod_path,
                "category": "Potential Drift",
                "changed_files": module_changed[:5],
                "recommendation": f"Review changes in '{mod_name}' — file changes detected but may be internal-only. Inspect and confirm.",
            })
            summary["potential"] += 1

    return {"drift_report": drift_report, "summary": summary}


def validate_graph_file(graph_file_path: str) -> dict:
    """
    Validate a graph_export.py JSON output file for blublu v2.0.0 schema compliance.
    Returns dict with keys: valid (bool), errors (list), warnings (list).
    """
    errors = []
    warnings = []
    p = Path(graph_file_path)

    if not p.is_file():
        return {"valid": False, "errors": [f"File not found: {graph_file_path}"], "warnings": []}

    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"], "warnings": []}
    except Exception as e:
        return {"valid": False, "errors": [f"Cannot read file: {e}"], "warnings": []}

    if "version" not in data:
        errors.append("Missing required field: 'version'")
    elif data["version"] != "2.0.0":
        warnings.append(f"Version is '{data['version']}', expected '2.0.0'")

    if "project" not in data:
        errors.append("Missing required field: 'project'")

    node_ids = set()
    if "nodes" not in data:
        errors.append("Missing required field: 'nodes'")
    elif not isinstance(data["nodes"], list):
        errors.append("'nodes' must be an array")
    else:
        required_node_fields = {"id", "name", "path", "type", "status"}
        for i, node in enumerate(data["nodes"]):
            missing = required_node_fields - set(node.keys())
            if missing:
                errors.append(f"Node[{i}] missing fields: {', '.join(sorted(missing))}")
            else:
                node_ids.add(node["id"])

    if "edges" in data and isinstance(data["edges"], list):
        required_edge_fields = {"source", "target", "type", "confidence"}
        for i, edge in enumerate(data["edges"]):
            missing = required_edge_fields - set(edge.keys())
            if missing:
                errors.append(f"Edge[{i}] missing fields: {', '.join(sorted(missing))}")
            else:
                if edge["source"] not in node_ids:
                    errors.append(f"Edge[{i}] source '{edge['source']}' references unknown node")
                if edge["target"] not in node_ids:
                    errors.append(f"Edge[{i}] target '{edge['target']}' references unknown node")

    if "metadata" not in data:
        warnings.append("Missing optional field: 'metadata'")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def _print_drift_report(drift_result: dict, format_output: str):
    """Print the drift report in text or JSON format."""
    report = drift_result["drift_report"]
    summary = drift_result["summary"]

    if format_output == "json":
        print(json.dumps(drift_result, indent=2))
        return

    print("=" * 60)
    print(" Architecture Drift Report (v2.0.0)")
    print("=" * 60)
    print(f"Confirmed Drift:        {summary['confirmed']}")
    print(f"Potential Drift:        {summary['potential']}")
    print(f"Unverified Modules:     {summary['unverified']}")
    print(f"User-Approved Exceptions: {summary['approved_exceptions']}")
    print("-" * 60)

    if not report:
        print("No drift detected. All verified modules are up to date.")
        print("=" * 60)
        return

    for entry in report:
        cat = entry["category"]
        icon = {
            "Confirmed Drift": "🔴",
            "Potential Drift": "🟡",
            "Unverified": "⚪",
            "User-Approved Exception": "✅",
        }.get(cat, "?")
        print(f"\n{icon} [{cat}] {entry['module']}")
        print(f"   Path:           {entry['path']}")
        if entry["changed_files"]:
            print(f"   Changed Files:  {', '.join(entry['changed_files'][:3])}")
            if len(entry["changed_files"]) > 3:
                print(f"                   ... and {len(entry['changed_files']) - 3} more")
        print(f"   Recommendation: {entry['recommendation']}")

    print("\n" + "=" * 60)
    print("NOTE: Drift detection is READ-ONLY. No blueprint changes were made.")
    print("      Use 'blublu update' or 'blublu rebuild' to sync the blueprint.")
    print("=" * 60)


def main():
    args = parse_args()

    # --validate-graph mode: validate a graph export file, then exit
    if args.validate_graph:
        result = validate_graph_file(args.validate_graph)
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            if result["valid"]:
                print(f"✔ Graph is VALID: {args.validate_graph}")
            else:
                print(f"✖ Graph is INVALID: {args.validate_graph}")
            for err in result["errors"]:
                print(f"  [ERR]  {err}")
            for warn in result["warnings"]:
                print(f"  [WARN] {warn}")
        sys.exit(0 if result["valid"] else 1)

    res = validate_blueprint(
        args.path,
        check_files=args.check_files,
        check_staleness_flag=args.check_staleness,
        strict=args.strict,
    )

    if args.format == "json":
        output = dict(res)
        # Optionally attach drift results to JSON output
        if args.check_drift:
            drift_result = check_drift(
                args.path,
                res.get("module_registry", []),
                args.drift_exceptions,
            )
            output["drift"] = drift_result
        print(json.dumps(output, indent=2))
    else:
        status_symbol = "✔ PASS" if res["valid"] else "✖ FAIL"
        mode_str = "Distributed" if res.get("distributed_mode") else "Single-File"
        print("=" * 60)
        print(f" blublu (blublu) Blueprint Validator v2.0.0 — {status_symbol} ({mode_str})")
        print("=" * 60)
        print(f"File:               {res['file']}")
        print(f"Total Modules:      {res['metrics']['total_modules']}")
        print(f"Verification Ratio: {res['metrics']['verification_ratio']}% ({res['metrics']['health_category']})")
        print(f"  - Verified:       {res['metrics']['verified']}")
        print(f"  - Inferred:       {res['metrics']['inferred']}")
        print(f"  - Unverified:     {res['metrics']['unverified']}")
        print(f"  - Stale:          {res['metrics']['stale']}")
        if res.get("distributed_mode"):
            sub_info = res["sub_blueprints"]
            print(f"Sub-Blueprints:     {len(sub_info['registered'])} registered, {len(sub_info['missing'])} missing, {len(sub_info['orphaned'])} orphaned")
        print("-" * 60)

        if res["warnings"]:
            print(f"Warnings ({len(res['warnings'])}):")
            for w in res["warnings"]:
                print(f"  [WARN] {w}")
            print("-" * 60)

        if res["errors"]:
            print(f"Errors ({len(res['errors'])}):")
            for e in res["errors"]:
                print(f"  [ERR]  {e}")
            print("-" * 60)

        if res["mermaid_fallback_tables"]:
            print("Mermaid Fallback Recommendation:")
            for fb in res["mermaid_fallback_tables"]:
                print(fb)
            print("-" * 60)

        if res["valid"]:
            print("Summary: Blueprint is structurally sound, valid, and compliant.")
        else:
            print("Summary: Blueprint has validation errors. Fix issues or run 'blublu validate'.")
        print("=" * 60)

        # --check-drift: print drift report after main validation output
        if args.check_drift:
            drift_result = check_drift(
                args.path,
                res.get("module_registry", []),
                args.drift_exceptions,
            )
            _print_drift_report(drift_result, args.format)
            # In strict mode, confirmed drift triggers non-zero exit
            if args.strict and drift_result["summary"]["confirmed"] > 0:
                sys.exit(2)

    # Exit codes: 0 = valid, 2 = broken paths / staleness in strict, 1 = structural error
    if res["valid"]:
        sys.exit(0)
    elif res["broken_paths"] or res.get("stale_modules"):
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
