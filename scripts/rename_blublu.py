#!/usr/bin/env python3
import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

for dirpath, dirnames, filenames in os.walk(root):
    # rename files containing 'codsblu'
    for filename in list(filenames):
        if 'codsblu' in filename:
            old_path = os.path.join(dirpath, filename)
            new_name = filename.replace('codsblu', 'blublu')
            new_path = os.path.join(dirpath, new_name)
            os.rename(old_path, new_path)
            print(f"Renamed file: {old_path} -> {new_path}")
    # replace content in all files
    for filename in filenames:
        file_path = os.path.join(dirpath, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue  # skip binary or unreadable
        if 'codsblu' in content:
            new_content = content.replace('codsblu', 'blublu')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Replaced content in: {file_path}")
