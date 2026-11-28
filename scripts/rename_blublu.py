#!/usr/bin/env python3
"""
Full rename: replace every occurrence of 'blublu' with 'blublu'
- in file/directory names
- in file contents (UTF-8 text files only)

Skip: .git internals, __pycache__, .pyc binaries
"""
import os
import shutil
import sys

ROOT = os.path.abspath(r"c:\All\VSC\blublu")
OLD = "blublu"
NEW = "blublu"
SKIP_DIRS = {".git", "__pycache__"}
SKIP_EXTS = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip", ".tar", ".gz"}

renamed_files = []
replaced_files = []
errors = []

# ── Pass 1: replace CONTENT in all text files ──────────────────────────────
for dirpath, dirnames, filenames in os.walk(ROOT, topdown=True):
    # skip hidden / cache dirs
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for filename in filenames:
        ext = os.path.splitext(filename)[1].lower()
        if ext in SKIP_EXTS:
            continue
        path = os.path.join(dirpath, filename)
        try:
            with open(path, "r", encoding="utf-8", errors="strict") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError, OSError):
            continue   # binary or unreadable
        if OLD in content:
            new_content = content.replace(OLD, NEW)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                replaced_files.append(path)
            except Exception as e:
                errors.append(f"Content replace error {path}: {e}")

# ── Pass 2: rename FILES that contain 'blublu' in their name ───────────────
# Walk bottom-up so leaf files are renamed before their parent dirs
for dirpath, dirnames, filenames in os.walk(ROOT, topdown=False):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for filename in filenames:
        if OLD in filename:
            old_path = os.path.join(dirpath, filename)
            new_name = filename.replace(OLD, NEW)
            new_path = os.path.join(dirpath, new_name)
            if os.path.exists(new_path):
                # target already exists (e.g. blublu.cmd already created) → remove old
                try:
                    os.remove(old_path)
                    renamed_files.append(f"  REMOVED duplicate src: {old_path}")
                except Exception as e:
                    errors.append(f"Remove error {old_path}: {e}")
            else:
                try:
                    shutil.move(old_path, new_path)
                    renamed_files.append(f"  {old_path}  →  {new_path}")
                except Exception as e:
                    errors.append(f"Rename error {old_path}: {e}")

    # rename directories themselves (bottom-up)
    for d in dirnames:
        if OLD in d:
            old_path = os.path.join(dirpath, d)
            new_name = d.replace(OLD, NEW)
            new_path = os.path.join(dirpath, new_name)
            try:
                shutil.move(old_path, new_path)
                renamed_files.append(f"  DIR {old_path}  →  {new_path}")
            except Exception as e:
                errors.append(f"Dir rename error {old_path}: {e}")

print(f"\n=== blublu rename complete ===")
print(f"Content replaced in {len(replaced_files)} files:")
for p in replaced_files:
    print(f"  {p}")
print(f"\nFiles/dirs renamed ({len(renamed_files)}):")
for p in renamed_files:
    print(p)
if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("\nNo errors. All done!")
