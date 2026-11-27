#!/usr/bin/env python3
"""
blublu v1.2.0 — Local Filesystem Change Watcher
Monitors the codebase for file changes with debouncing, recording pending changes
into .agents/.pending-changes.json for consumption by AI agents.

SECURITY RULE: Processes deterministic filesystem metadata only.
Never triggers remote LLM API calls automatically.

Dependencies: Pure Python 3 standard library.
"""

import sys
import os
import time
import json
import signal
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory for scanner import
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    import scanner
except ImportError:
    scanner = None


PID_FILE_REL = Path(".agents") / ".codsblu.pid"
PENDING_FILE_REL = Path(".agents") / ".pending-changes.json"


def get_pid_file(root_path: Path) -> Path:
    return root_path / PID_FILE_REL


def get_pending_file(root_path: Path) -> Path:
    return root_path / PENDING_FILE_REL


def is_process_running(pid: int) -> bool:
    """Checks whether a process with given PID is currently active."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import subprocess
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            return str(pid) in out
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def stop_watcher(root_path: Path) -> bool:
    """Stops any currently running background watcher process."""
    pid_file = get_pid_file(root_path)
    if not pid_file.is_file():
        return False

    try:
        pid_str = pid_file.read_text(encoding="utf-8").strip()
        pid = int(pid_str)
    except Exception:
        pid_file.unlink(missing_ok=True)
        return False

    if not is_process_running(pid):
        pid_file.unlink(missing_ok=True)
        return False

    # Terminate process
    try:
        if sys.platform == "win32":
            import subprocess
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            if is_process_running(pid):
                os.kill(pid, signal.SIGKILL)
    except Exception:
        pass

    pid_file.unlink(missing_ok=True)
    return True


def record_pending_changes(root_path: Path, changed_files: list):
    """Batches and writes modified file list into .agents/.pending-changes.json."""
    if not changed_files:
        return

    pending_file = get_pending_file(root_path)
    existing_files = set()

    if pending_file.is_file():
        try:
            with open(pending_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_files.update(data.get("pending_files", []))
        except Exception:
            existing_files = set()

    existing_files.update(changed_files)
    payload = {
        "last_event_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pending_count": len(existing_files),
        "pending_files": sorted(list(existing_files)),
    }

    try:
        pending_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pending_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as exc:
        print(f"[WARN] Failed to write pending changes: {exc}", file=sys.stderr)


def start_watcher(root_path: Path, debounce_ms: int = 2000, max_iterations: int = 0):
    """
    Main watcher loop.
    Polls directory changes, debounces events, and updates .agents/.pending-changes.json.
    """
    pid_file = get_pid_file(root_path)
    if pid_file.is_file():
        try:
            existing_pid = int(pid_file.read_text(encoding="utf-8").strip())
            if is_process_running(existing_pid):
                print(f"[INFO] Watcher is already running (PID: {existing_pid}).", file=sys.stderr)
                return
        except Exception:
            pass

    # Write current PID
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    current_pid = os.getpid()
    pid_file.write_text(str(current_pid), encoding="utf-8")

    def cleanup(*args):
        try:
            pid_file.unlink(missing_ok=True)
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print(f"[*] Codsblu Watcher started on '{root_path}' (PID: {current_pid}, Debounce: {debounce_ms}ms)")
    poll_interval = max(0.5, debounce_ms / 1000.0)

    # Initial snapshot to avoid immediately triggering on existing files
    if scanner:
        scanner.scan_changes(str(root_path), save_cache=True)

    iterations = 0
    try:
        while True:
            time.sleep(poll_interval)
            iterations += 1

            if scanner:
                res = scanner.scan_changes(str(root_path), save_cache=True)
                all_changed = res.get("all_changed", [])
                if all_changed:
                    # Filter out .agents directory internal changes
                    valid_changes = [
                        f for f in all_changed
                        if not f.startswith(".agents/") and not f.startswith(".agents\\")
                    ]
                    if valid_changes:
                        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Detected {len(valid_changes)} changed file(s): {', '.join(valid_changes[:3])}")
                        record_pending_changes(root_path, valid_changes)

            if max_iterations > 0 and iterations >= max_iterations:
                break

    finally:
        cleanup()


def main():
    parser = argparse.ArgumentParser(description="Codsblu Local Filesystem Watcher")
    parser.add_argument("--path", default=".", help="Project root to watch")
    parser.add_argument("--debounce", type=int, default=2000, help="Debounce delay in ms (default: 2000)")
    parser.add_argument("--stop", action="store_true", help="Stop running background watcher")
    parser.add_argument("--status", action="store_true", help="Check status of background watcher")
    parser.add_argument("--iterations", type=int, default=0, help="Stop after N iterations (for testing)")
    args = parser.parse_args()

    target = Path(args.path).resolve()

    if args.stop:
        stopped = stop_watcher(target)
        if stopped:
            print("✔ Codsblu watcher stopped.")
        else:
            print("No active watcher process was found.")
        sys.exit(0)

    if args.status:
        pid_file = get_pid_file(target)
        if pid_file.is_file():
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
                if is_process_running(pid):
                    print(f"✔ Codsblu watcher is RUNNING (PID: {pid}).")
                    pending = get_pending_file(target)
                    if pending.is_file():
                        with open(pending, "r", encoding="utf-8") as f:
                            d = json.load(f)
                            print(f"  Pending changed files in queue: {d.get('pending_count', 0)}")
                    sys.exit(0)
            except Exception:
                pass
        print("Codsblu watcher is NOT running.")
        sys.exit(0)

    start_watcher(target, debounce_ms=args.debounce, max_iterations=args.iterations)


if __name__ == "__main__":
    main()
