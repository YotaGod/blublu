#!/usr/bin/env python3
"""
blublu v1.1.0 — Advanced Filesystem & Git Fallback Scanner
Detects modified, added, and deleted files across Git-enabled and non-Git repositories.
Provides fast filesystem metadata caching to detect changes when Git is unavailable.

Dependencies: Pure Python 3 standard library (sys, os, subprocess, hashlib, json, pathlib, argparse).
"""

import sys
import os
import subprocess
import hashlib
import json
import argparse
from pathlib import Path


IGNORED_DIRECTORIES = {
    "node_modules",
    "vendor",
    ".git",
    "dist",
    "build",
    "out",
    "target",
    "bin",
    "obj",
    "coverage",
    ".nyc_output",
    ".next",
    ".nuxt",
    ".output",
    ".cache",
    ".turbo",
    ".parcel-cache",
    "tmp",
    "temp",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".pytest_cache",
    ".agents/scratch",
}

IGNORED_FILE_EXTENSIONS = {
    ".min.js",
    ".min.css",
    ".map",
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
}

CACHE_FILE_REL = Path(".agents") / ".cache_scan.json"


def is_git_repository(root_path: Path) -> bool:
    """Checks whether target path is a Git repository root."""
    if (root_path / ".git").exists():
        return True
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(root_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            top_level = Path(res.stdout.strip()).resolve()
            return top_level == root_path.resolve()
        return False
    except Exception:
        return False


def get_git_changes(root_path: Path) -> dict:
    """Uses git status and diff commands to extract changed files."""
    changes = {
        "mode": "git",
        "added": [],
        "modified": [],
        "deleted": [],
        "all_changed": [],
    }

    try:
        # Run git status --short
        res = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=str(root_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                code = line[:2].strip()
                file_rel = line[2:].strip().strip('"')
                # Normalize slashes
                file_rel = file_rel.replace("\\", "/")

                if code in ("??", "A"):
                    changes["added"].append(file_rel)
                elif code in ("M", "MM"):
                    changes["modified"].append(file_rel)
                elif code == "D":
                    changes["deleted"].append(file_rel)
                elif code.startswith("R"):
                    # Rename e.g. R  old -> new
                    parts = file_rel.split(" -> ")
                    if len(parts) == 2:
                        changes["deleted"].append(parts[0].strip())
                        changes["added"].append(parts[1].strip())

        # Also inspect uncommitted working tree diff vs HEAD
        diff_res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(root_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        if diff_res.returncode == 0:
            for f in diff_res.stdout.splitlines():
                f = f.strip().replace("\\", "/")
                if f and f not in changes["modified"] and f not in changes["added"] and f not in changes["deleted"]:
                    changes["modified"].append(f)

    except Exception as exc:
        # If git command fails, fall back gracefully
        changes["error"] = str(exc)

    # Combine unique list
    all_set = set(changes["added"] + changes["modified"] + changes["deleted"])
    changes["all_changed"] = sorted(list(all_set))
    return changes


def compute_file_hash(filepath: Path) -> str:
    """Computes SHA256 of file (first 64KB for speed, or entire file if small)."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(65536)
            hasher.update(chunk)
            if len(chunk) == 65536:
                # Read remainder if smaller than 1MB
                rest = f.read(1048576)
                hasher.update(rest)
        return hasher.hexdigest()
    except Exception:
        return ""


def should_ignore(rel_path: str) -> bool:
    """Determines whether a relative path matches any ignore rules."""
    parts = Path(rel_path).parts
    for part in parts:
        if part in IGNORED_DIRECTORIES:
            return True
        if part.startswith(".") and part not in (".agents",):
            # Ignore hidden dirs e.g. .cache, .turbo
            return True

    for ext in IGNORED_FILE_EXTENSIONS:
        if rel_path.endswith(ext):
            return True

    return False


def get_filesystem_changes(root_path: Path, save_cache: bool = True) -> dict:
    """
    Performs recursive filesystem scan comparing against .agents/.cache_scan.json.
    Guarantees loop-free traversal (follow_symlinks=False).
    """
    cache_file = root_path / CACHE_FILE_REL
    old_cache = {}

    if cache_file.is_file():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                old_cache = json.load(f)
        except Exception:
            old_cache = {}

    current_scan = {}
    changes = {
        "mode": "filesystem_fallback",
        "added": [],
        "modified": [],
        "deleted": [],
        "all_changed": [],
        "initial_scan": len(old_cache) == 0,
    }

    # Walk filesystem safely with followlinks=False to prevent infinite symlink loops
    for root, dirs, files in os.walk(str(root_path), topdown=True, followlinks=False):
        # Prune ignored directories in-place for performance
        dirs[:] = [d for d in dirs if not should_ignore(d) and d not in IGNORED_DIRECTORIES]

        for fname in files:
            full_file = Path(root) / fname
            try:
                rel_file = str(full_file.relative_to(root_path)).replace("\\", "/")
            except ValueError:
                continue

            if should_ignore(rel_file):
                continue

            # Don't track cache file itself
            if rel_file == str(CACHE_FILE_REL).replace("\\", "/"):
                continue

            try:
                stat = full_file.stat()
                mtime = stat.st_mtime
                size = stat.st_size
                current_scan[rel_file] = {
                    "mtime": mtime,
                    "size": size,
                }
            except (OSError, PermissionError):
                continue

    # Detect additions and modifications
    for f_path, meta in current_scan.items():
        if f_path not in old_cache:
            if not changes["initial_scan"]:
                changes["added"].append(f_path)
            # Compute hash for new entry
            meta["hash"] = compute_file_hash(root_path / f_path)
        else:
            old_meta = old_cache[f_path]
            # Fast check: mtime and size
            if meta["mtime"] != old_meta.get("mtime") or meta["size"] != old_meta.get("size"):
                new_hash = compute_file_hash(root_path / f_path)
                meta["hash"] = new_hash
                if new_hash != old_meta.get("hash"):
                    changes["modified"].append(f_path)
            else:
                meta["hash"] = old_meta.get("hash", "")

    # Detect deletions
    for f_path in old_cache:
        if f_path not in current_scan:
            changes["deleted"].append(f_path)

    # Save cache if requested or if initial scan
    if save_cache or changes["initial_scan"]:
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(current_scan, f, indent=2)
        except Exception:
            pass

    all_set = set(changes["added"] + changes["modified"] + changes["deleted"])
    changes["all_changed"] = sorted(list(all_set))
    return changes


def scan_changes(project_root: str = ".", save_cache: bool = True) -> dict:
    """Primary entry point: auto-selects Git or filesystem scanner."""
    root = Path(project_root).resolve()

    if is_git_repository(root):
        return get_git_changes(root)
    else:
        return get_filesystem_changes(root, save_cache=save_cache)


def main():
    parser = argparse.ArgumentParser(
        description="blublu v1.1.0 Change Scanner (Git + Filesystem Fallback)"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Project root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--save-cache",
        action="store_true",
        default=True,
        help="Save/update .agents/.cache_scan.json in non-git mode",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: 'text' (default) or 'json'",
    )
    args = parser.parse_args()

    results = scan_changes(args.path, save_cache=args.save_cache)

    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        print("=" * 60)
        print(f" blublu Change Scanner — Mode: {results['mode']}")
        print("=" * 60)
        print(f"Total Changes Detected: {len(results['all_changed'])}")
        print(f"  - Added:    {len(results['added'])}")
        print(f"  - Modified: {len(results['modified'])}")
        print(f"  - Deleted:  {len(results['deleted'])}")
        print("-" * 60)

        if results["added"]:
            print("Added files:")
            for a in results["added"]:
                print(f"  [+] {a}")
        if results["modified"]:
            print("Modified files:")
            for m in results["modified"]:
                print(f"  [*] {m}")
        if results["deleted"]:
            print("Deleted files:")
            for d in results["deleted"]:
                print(f"  [-] {d}")
        if not results["all_changed"]:
            print("No file changes detected in working copy.")
        print("=" * 60)


if __name__ == "__main__":
    main()
