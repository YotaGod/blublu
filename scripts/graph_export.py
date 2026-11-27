#!/usr/bin/env python3
"""
blublu v2.0.0 - Architecture Graph Exporter
Exports Module Registry + Dependency Map to structured JSON and YAML.
Derived output only — never modifies blueprint files.

Usage:
  python scripts/graph_export.py [--path <dir>] [--format json|yaml|both] [--output <base>]
  python scripts/graph_export.py --validate-graph <file.json>
  python scripts/graph_export.py --include-sub-blueprints

Dependencies: Pure Python 3 standard library (no pip packages required).
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export blublu architecture graph to JSON or YAML."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml", "both"],
        default="json",
        help="Output format: json, yaml, or both (default: json)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output file base path without extension. Omit to print to stdout.",
    )
    parser.add_argument(
        "--validate-graph",
        default="",
        metavar="FILE",
        help="Validate an existing graph JSON file for schema compliance.",
    )
    parser.add_argument(
        "--include-sub-blueprints",
        action="store_true",
        help="Also parse sub-blueprints for domain-level nodes and edges.",
    )
    return parser.parse_args()


def resolve_root(path_str: str) -> Path:
    p = Path(path_str).resolve()
    if p.is_file() and p.name == "codebase-map.md":
        return p.parent.parent if p.parent.name == ".agents" else p.parent
    return p


def infer_node_type(path_str: str) -> str:
    s = path_str.lower()
    if any(x in s for x in ["infra", "terraform", "k8s", "helm", "docker", "deploy"]):
        return "infra"
    if any(x in s for x in ["packages/", "libs/", "shared-", "shared_", "/lib/"]):
        return "lib"
    if any(x in s for x in ["frontend", "/web/", "dashboard", "portal", "ui/", "/client"]):
        return "frontend"
    if any(x in s for x in ["apps/", "services/", "-service", "_service"]):
        return "service"
    return "unknown"


def slugify(name: str) -> str:
    """Convert a module name or path to a safe identifier."""
    cleaned = name.strip().strip("`").strip("*").strip()
    return re.sub(r"[^a-zA-Z0-9_-]", "_", cleaned)


def parse_module_registry(content: str, domain: str = "") -> list:
    """
    Extract nodes from Module Registry Markdown table in blueprint content.
    Handles both Level 1 (domain-aggregated) and Level 2 (module-level) registries.
    """
    nodes = []

    # Isolate Section 5 body
    sec5_match = re.search(
        r"##\s+5\.[^\n]*\n(.*?)(?=\n##\s+6\.|\Z)", content, re.DOTALL
    )
    if not sec5_match:
        # Try to find any Module Registry heading
        sec5_match = re.search(
            r"(?:Module Registry|##\s+3\.[^\n]*Module)[^\n]*\n(.*?)(?=\n##|\Z)",
            content, re.DOTALL | re.IGNORECASE
        )

    if sec5_match:
        body = sec5_match.group(1)
        # Only use content before ### sub-headings (like Sub-Blueprints Index)
        split = re.split(r"\n###", body)
        body = split[0] if split else body
    else:
        body = content

    # Parse Markdown table rows
    rows = []
    header_found = False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # Skip separator rows (e.g. |---|---|)
        if re.match(r"^\|[\s\-:| ]+\|$", stripped):
            if not header_found:
                header_found = True
            continue
        cols = [c.strip() for c in stripped.split("|")]
        cols = [c for c in cols if c]  # remove empty splits from leading/trailing |
        if len(cols) >= 2:
            rows.append(cols)

    # Skip the header row if present (first row likely has column names)
    data_rows = rows
    if rows and rows[0] and rows[0][0].lower() in ("module", "name", "domain", "service"):
        data_rows = rows[1:]

    for row in data_rows:
        if len(row) < 2:
            continue
        name = slugify(row[0])
        path = row[1].strip("`").strip() if len(row) > 1 else ""
        # Skip obviously header-like rows
        if name.lower() in ("module", "name", "domain", "service", "source"):
            continue
        if not name or name.startswith("-"):
            continue

        status_col = row[-1] if len(row) >= 3 else "[Unverified]"
        status_match = re.search(r"\[(Verified|Inferred|Unverified|Stale)\]", status_col)
        status = status_match.group(1) if status_match else "Unverified"

        nodes.append({
            "id": name,
            "name": name,
            "domain": domain or "root",
            "path": path,
            "type": infer_node_type(path),
            "status": status,
        })

    return nodes


def parse_mermaid_edges(content: str, known_node_ids: set) -> list:
    """Extract edges from Mermaid graph blocks in blueprint content."""
    edges = []
    mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)```", content, re.DOTALL)

    for block in mermaid_blocks:
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("graph") or line.startswith("flowchart"):
                continue

            # Match arrows: NodeA --> NodeB, NodeA -.-> NodeB, NodeA ==> NodeB
            # Also with labels: NodeA -->|label| NodeB
            # Node IDs can have optional display labels: NodeA["Display"]
            arrow_pattern = re.compile(
                r'(\w+)(?:\[.*?\]|\(\(.*?\)\))?\s*'
                r'(-->|-.->|==>)(?:\|([^|]+)\|)?\s*'
                r'(\w+)'
            )
            m = arrow_pattern.search(line)
            if m:
                src, arrow, label, tgt = m.groups()
                if arrow == "-->":
                    edge_type = "import"
                elif arrow == "-.->":
                    edge_type = "event"
                else:
                    edge_type = "api"

                confidence = (
                    "Confirmed"
                    if (src in known_node_ids and tgt in known_node_ids)
                    else "Inferred"
                )

                edges.append({
                    "source": src,
                    "target": tgt,
                    "type": edge_type,
                    "label": (label.strip() if label else f"{src}->{tgt}"),
                    "confidence": confidence,
                })

    return edges


def parse_dependency_table_edges(content: str) -> list:
    """
    Parse dependency tables with Source|Target|Type|Label|Evidence|Confidence columns.
    """
    edges = []
    # Find tables that have a 'Source' column header
    table_pattern = re.compile(
        r"\|[^\n]*\bSource\b[^\n]*\|\n\|[-: |]+\|\n((?:\|[^\n]+\|\n?)+)",
        re.IGNORECASE
    )
    for match in table_pattern.finditer(content):
        block = match.group(1)
        for line in block.strip().splitlines():
            cols = [c.strip() for c in line.split("|")]
            cols = [c for c in cols if c]
            if len(cols) < 4:
                continue
            src = slugify(cols[0])
            tgt = slugify(cols[1])
            edge_type_raw = cols[2].strip().lower() if len(cols) > 2 else "api"
            # Normalize edge type
            if edge_type_raw in ("import", "api", "event", "db-shared", "lib"):
                edge_type = edge_type_raw
            else:
                edge_type = "api"
            label = cols[3] if len(cols) > 3 else ""
            confidence_raw = cols[-1] if len(cols) >= 5 else "Inferred"
            if "confirmed" in confidence_raw.lower():
                confidence = "Confirmed"
            elif "unverified" in confidence_raw.lower():
                confidence = "Unverified"
            else:
                confidence = "Inferred"

            if src and tgt and src.lower() not in ("source", "module"):
                edges.append({
                    "source": src,
                    "target": tgt,
                    "type": edge_type,
                    "label": label,
                    "confidence": confidence,
                })
    return edges


def parse_sub_blueprints_index(content: str) -> list:
    """
    Parse Sub-Blueprints Index table from blueprint content.
    Returns list of dicts with 'domain' and 'path' keys.
    """
    entries = []
    idx_match = re.search(
        r"### Sub-Blueprints Index[^\n]*\n\|[^\n]*\|\n\|[-: |]+\|\n((?:\|[^\n]+\|\n?)+)",
        content, re.IGNORECASE
    )
    if not idx_match:
        return entries

    for line in idx_match.group(1).strip().splitlines():
        cols = [c.strip() for c in line.split("|")]
        cols = [c for c in cols if c]
        if len(cols) >= 2:
            domain_name = slugify(cols[0])
            path_col = cols[1].strip("`").strip()
            if ".md" in path_col and domain_name.lower() not in ("domain", "service"):
                entries.append({"domain": domain_name, "path": path_col})
    return entries


def detect_circular_deps(nodes: list, edges: list) -> list:
    """
    Detect circular dependencies using iterative DFS.
    Returns list of cycle path strings, e.g. ["A → B → C → A"].
    """
    # Build adjacency list
    adj = {n["id"]: [] for n in nodes}
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        if src in adj:
            adj[src].append(tgt)

    visited = set()
    cycles = []

    def dfs(start):
        # Iterative DFS with path tracking
        stack = [(start, [start])]
        seen_in_path = {start}
        while stack:
            node, path = stack.pop()
            for neighbor in adj.get(node, []):
                if neighbor == start:
                    cycle_str = " → ".join(path + [neighbor])
                    if cycle_str not in cycles:
                        cycles.append(cycle_str)
                elif neighbor not in seen_in_path:
                    seen_in_path.add(neighbor)
                    stack.append((neighbor, path + [neighbor]))

    for node_id in list(adj.keys()):
        if node_id not in visited:
            visited.add(node_id)
            dfs(node_id)

    return cycles


def build_graph(root: Path, include_sub_blueprints: bool) -> dict:
    """Build the full architecture graph from blueprint files."""
    blueprint = root / ".agents" / "codebase-map.md"
    if not blueprint.is_file():
        print(f"[ERR] Blueprint not found: {blueprint}", file=sys.stderr)
        sys.exit(1)

    content = blueprint.read_text(encoding="utf-8")

    # Extract project name from Section 1
    name_match = re.search(r"\*\*Name\*\*[:\s]+([^\n]+)", content)
    project_name = name_match.group(1).strip() if name_match else root.name

    # Parse root-level nodes
    nodes = parse_module_registry(content, domain="root")
    node_ids = {n["id"] for n in nodes}

    # Parse edges from Mermaid and dependency tables
    edges = parse_mermaid_edges(content, node_ids)
    edges += parse_dependency_table_edges(content)

    # Include sub-blueprints if requested
    if include_sub_blueprints:
        sub_dir = root / ".agents" / "sub-blueprints"
        if sub_dir.is_dir():
            for md_file in sorted(sub_dir.rglob("*.md")):
                # Determine domain from path relative to sub-blueprints dir
                rel = md_file.relative_to(sub_dir)
                parts = list(rel.parts)
                domain = parts[0].replace(".md", "") if parts else md_file.stem
                sub_content = md_file.read_text(encoding="utf-8")

                sub_nodes = parse_module_registry(sub_content, domain=domain)
                for sn in sub_nodes:
                    if sn["id"] not in node_ids:
                        nodes.append(sn)
                        node_ids.add(sn["id"])

                # Parse edges from this sub-blueprint
                current_ids = {n["id"] for n in nodes}
                sub_edges = parse_mermaid_edges(sub_content, current_ids)
                sub_edges += parse_dependency_table_edges(sub_content)
                edges += sub_edges

    # Deduplicate edges
    seen_edges = set()
    unique_edges = []
    for e in edges:
        key = (e.get("source", ""), e.get("target", ""), e.get("type", ""))
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)

    # Detect circular dependencies
    cycles = detect_circular_deps(nodes, unique_edges)

    # Count unverified edges
    unverified_count = sum(1 for e in unique_edges if e.get("confidence") == "Unverified")

    graph = {
        "version": "2.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "name": project_name,
            "root_path": str(root),
        },
        "nodes": nodes,
        "edges": unique_edges,
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(unique_edges),
            "circular_dependencies": cycles,
            "unverified_edges": unverified_count,
        },
    }
    return graph


# ---------------------------------------------------------------------------
# Simple YAML Serializer (stdlib only)
# ---------------------------------------------------------------------------

def _yaml_scalar(val) -> str:
    """Serialize a scalar value to YAML string."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        # Quote strings with special YAML characters
        needs_quote = any(c in val for c in [':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'", '\n', '\r'])
        if not val or needs_quote or val.lower() in ("true", "false", "null", "yes", "no", "on", "off"):
            escaped = val.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            return f'"{escaped}"'
        return val
    return str(val)


def _to_yaml_lines(obj, indent: int = 0) -> list:
    """Recursively convert obj to YAML lines."""
    pad = "  " * indent
    lines = []
    if obj is None:
        lines.append("null")
    elif isinstance(obj, bool):
        lines.append("true" if obj else "false")
    elif isinstance(obj, (int, float)):
        lines.append(str(obj))
    elif isinstance(obj, str):
        lines.append(_yaml_scalar(obj))
    elif isinstance(obj, list):
        if not obj:
            lines.append("[]")
        else:
            for item in obj:
                if isinstance(item, dict):
                    first = True
                    for k, v in item.items():
                        prefix = f"{pad}- " if first else f"{pad}  "
                        first = False
                        v_lines = _to_yaml_lines(v, indent + 1)
                        if len(v_lines) == 1:
                            lines.append(f"{prefix}{k}: {v_lines[0]}")
                        else:
                            lines.append(f"{prefix}{k}:")
                            lines.extend(v_lines)
                elif isinstance(item, list):
                    sub = _to_yaml_lines(item, indent + 1)
                    lines.append(f"{pad}-")
                    lines.extend(sub)
                else:
                    lines.append(f"{pad}- {_yaml_scalar(item)}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            v_lines = _to_yaml_lines(v, indent + 1)
            if len(v_lines) == 1 and not isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}: {v_lines[0]}")
            elif isinstance(v, list) and v:
                lines.append(f"{pad}{k}:")
                lines.extend(v_lines)
            elif isinstance(v, dict) and v:
                lines.append(f"{pad}{k}:")
                lines.extend(v_lines)
            else:
                lines.append(f"{pad}{k}: {v_lines[0] if v_lines else 'null'}")
    return lines


def graph_to_yaml(graph: dict) -> str:
    """Convert graph dict to YAML string."""
    result_lines = ["---"]
    for k, v in graph.items():
        v_lines = _to_yaml_lines(v, indent=1)
        if len(v_lines) == 1 and not isinstance(v, (dict, list)):
            result_lines.append(f"{k}: {v_lines[0]}")
        else:
            result_lines.append(f"{k}:")
            result_lines.extend(v_lines)
    result_lines.append("")  # trailing newline
    return "\n".join(result_lines)


# ---------------------------------------------------------------------------
# Graph Validation
# ---------------------------------------------------------------------------

def validate_graph_file(file_path: str) -> dict:
    """Validate a graph JSON file for blublu v2.0.0 schema compliance."""
    errors = []
    warnings = []
    p = Path(file_path)

    if not p.is_file():
        return {"valid": False, "errors": [f"File not found: {file_path}"], "warnings": []}

    # Determine format from extension
    try:
        with open(p, encoding="utf-8") as f:
            content = f.read()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"], "warnings": []}
    except Exception as e:
        return {"valid": False, "errors": [f"Cannot read file: {e}"], "warnings": []}

    # --- Field validation ---

    # version
    if "version" not in data:
        errors.append("Missing required field: 'version'")
    elif data["version"] != "2.0.0":
        warnings.append(f"Version is '{data['version']}', expected '2.0.0'")

    # generated_at
    if "generated_at" not in data:
        warnings.append("Missing optional field: 'generated_at'")

    # project
    if "project" not in data:
        errors.append("Missing required field: 'project'")
    elif not isinstance(data["project"], dict):
        errors.append("'project' must be an object")
    else:
        if "name" not in data["project"]:
            warnings.append("'project.name' is missing")

    # nodes — also collect names for loose edge-matching (mermaid uses diagram tokens)
    node_ids = set()
    node_names = set()
    if "nodes" not in data:
        errors.append("Missing required field: 'nodes'")
    elif not isinstance(data["nodes"], list):
        errors.append("'nodes' must be an array")
    elif len(data["nodes"]) == 0:
        warnings.append("'nodes' array is empty — no modules tracked")
    else:
        required_node_fields = {"id", "name", "path", "type", "status"}
        valid_types = {"service", "lib", "frontend", "infra", "unknown"}
        valid_statuses = {"Verified", "Inferred", "Unverified", "Stale"}
        for i, node in enumerate(data["nodes"]):
            if not isinstance(node, dict):
                errors.append(f"Node[{i}] must be an object")
                continue
            missing = required_node_fields - set(node.keys())
            if missing:
                errors.append(f"Node[{i}] missing fields: {', '.join(sorted(missing))}")
            else:
                node_ids.add(node["id"])
                node_names.add(node["name"])
                if node.get("type") not in valid_types:
                    warnings.append(f"Node[{i}] '{node.get('id')}' has unknown type: '{node.get('type')}'")
                if node.get("status") not in valid_statuses:
                    warnings.append(f"Node[{i}] '{node.get('id')}' has unknown status: '{node.get('status')}'")

    # edges
    if "edges" in data:
        if not isinstance(data["edges"], list):
            errors.append("'edges' must be an array")
        else:
            required_edge_fields = {"source", "target", "type", "confidence"}
            valid_edge_types = {"import", "api", "event", "db-shared", "lib"}
            valid_confidences = {"Confirmed", "Inferred", "Unverified"}
            for i, edge in enumerate(data["edges"]):
                if not isinstance(edge, dict):
                    errors.append(f"Edge[{i}] must be an object")
                    continue
                missing = required_edge_fields - set(edge.keys())
                if missing:
                    errors.append(f"Edge[{i}] missing fields: {', '.join(sorted(missing))}")
                else:
                    valid_refs = node_ids | node_names
                    if edge["source"] not in valid_refs:
                        # Downgrade to warning: mermaid tokens may differ from registry names
                        warnings.append(f"Edge[{i}] source '{edge['source']}' not found in node IDs or names (mermaid alias?)")
                    if edge["target"] not in valid_refs:
                        warnings.append(f"Edge[{i}] target '{edge['target']}' not found in node IDs or names (mermaid alias?)")
                    if edge.get("type") not in valid_edge_types:
                        warnings.append(f"Edge[{i}] has unknown type: '{edge.get('type')}'")
                    if edge.get("confidence") not in valid_confidences:
                        warnings.append(f"Edge[{i}] has unknown confidence: '{edge.get('confidence')}'")

    # metadata
    if "metadata" not in data:
        warnings.append("Missing optional field: 'metadata'")
    elif isinstance(data.get("metadata"), dict):
        meta = data["metadata"]
        if "node_count" in meta and meta["node_count"] != len(data.get("nodes", [])):
            warnings.append(
                f"metadata.node_count ({meta['node_count']}) does not match "
                f"actual nodes length ({len(data.get('nodes', []))})"
            )

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # --validate-graph mode
    if args.validate_graph:
        result = validate_graph_file(args.validate_graph)
        if result["valid"]:
            print(f"✔ Graph is VALID: {args.validate_graph}")
            if result["warnings"]:
                for w in result["warnings"]:
                    print(f"  [WARN] {w}")
        else:
            print(f"✖ Graph is INVALID: {args.validate_graph}")
            for err in result["errors"]:
                print(f"  [ERR]  {err}")
            for w in result["warnings"]:
                print(f"  [WARN] {w}")
        sys.exit(0 if result["valid"] else 1)

    # Normal export mode
    root = resolve_root(args.path)
    if not (root / ".agents" / "codebase-map.md").is_file():
        print(f"[ERR] No .agents/codebase-map.md found at: {root}", file=sys.stderr)
        sys.exit(1)

    graph = build_graph(root, args.include_sub_blueprints)
    json_str = json.dumps(graph, indent=2)
    yaml_str = graph_to_yaml(graph)

    if args.output:
        base = args.output
        if args.format in ("json", "both"):
            out_path = Path(base + ".json")
            out_path.write_text(json_str, encoding="utf-8")
            print(f"✔ JSON graph written to: {out_path}")
        if args.format in ("yaml", "both"):
            out_path = Path(base + ".yaml")
            out_path.write_text(yaml_str, encoding="utf-8")
            print(f"✔ YAML graph written to: {out_path}")
    else:
        if args.format in ("json", "both"):
            print(json_str)
        if args.format == "both":
            print("\n---")
        if args.format in ("yaml", "both"):
            print(yaml_str)

    # Summary to stderr so it doesn't pollute piped output
    m = graph["metadata"]
    circ = len(m["circular_dependencies"])
    circ_note = f" ⚠ {circ} circular dep(s) detected!" if circ else ""
    print(
        f"\n[INFO] Nodes: {m['node_count']}, Edges: {m['edge_count']}, "
        f"Unverified Edges: {m['unverified_edges']}{circ_note}",
        file=sys.stderr,
    )
    if circ:
        for cycle in m["circular_dependencies"]:
            print(f"  [CIRCULAR] {cycle}", file=sys.stderr)


if __name__ == "__main__":
    main()
