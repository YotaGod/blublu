#!/usr/bin/env python3
"""
blublu v1.1.0 — Architectural Blueprint Validator
Validates the structural integrity, section coverage, module registry consistency,
Mermaid diagram syntax, filesystem references, and staleness/drift detection.

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
    """
    lines = [line.strip() for line in body.splitlines() if line.strip()]
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

    result["valid"] = len(result["errors"]) == 0
    return result


def main():
    args = parse_args()
    res = validate_blueprint(
        args.path,
        check_files=args.check_files,
        check_staleness_flag=args.check_staleness,
        strict=args.strict,
    )

    if args.format == "json":
        print(json.dumps(res, indent=2))
    else:
        status_symbol = "✔ PASS" if res["valid"] else "✖ FAIL"
        print("=" * 60)
        print(f" Codsblu (blublu) Blueprint Validator v1.1.0 — {status_symbol}")
        print("=" * 60)
        print(f"File:               {res['file']}")
        print(f"Total Modules:      {res['metrics']['total_modules']}")
        print(f"Verification Ratio: {res['metrics']['verification_ratio']}% ({res['metrics']['health_category']})")
        print(f"  - Verified:       {res['metrics']['verified']}")
        print(f"  - Inferred:       {res['metrics']['inferred']}")
        print(f"  - Unverified:     {res['metrics']['unverified']}")
        print(f"  - Stale:          {res['metrics']['stale']}")
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

    # Exit codes: 0 = valid, 2 = broken paths / staleness in strict, 1 = structural error
    if res["valid"]:
        sys.exit(0)
    elif res["broken_paths"] or res.get("stale_modules"):
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
