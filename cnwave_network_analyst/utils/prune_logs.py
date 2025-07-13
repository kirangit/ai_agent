#!/usr/bin/env python3
"""
utils/prune_logs.py
------------------------------------
Delete all but the newest N log directories inside project_root/logs.

Assumptions
-----------
• Each log dir name starts with an 8-digit date + '_' + 6-digit time,
  e.g. 20250713_044503
• Script itself lives in project_root/utils
"""

from pathlib import Path
import shutil
import re
import sys

KEEP_COUNT = 3                                   # how many to retain
LOG_NAME_RE = re.compile(r"\d{8}_\d{6}")         # 20250713_044503

# ---------------------------------------------------------------------------
# Locate <project_root>/logs from this file's position
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_ROOT = PROJECT_ROOT / "logs"

def main():
    if not LOG_ROOT.exists():
        print(f"❌ Log directory not found: {LOG_ROOT}", file=sys.stderr)
        sys.exit(1)

    # collect candidate dirs
    log_dirs = [
        d for d in LOG_ROOT.iterdir()
        if d.is_dir() and LOG_NAME_RE.fullmatch(d.name)
    ]

    if len(log_dirs) <= KEEP_COUNT:
        print("Nothing to prune – fewer than or equal to "
              f"{KEEP_COUNT} log directories present.")
        return

    # oldest → newest
    log_dirs.sort(key=lambda p: p.name)
    to_delete = log_dirs[:-KEEP_COUNT]

    for d in to_delete:
        try:
            shutil.rmtree(d)
            print(f"🗑️  Deleted {d.relative_to(PROJECT_ROOT)}")
        except Exception as e:
            print(f"⚠️  Could not delete {d}: {e}", file=sys.stderr)

    print(f"✅ Kept {KEEP_COUNT} newest log directories, "
          f"pruned {len(to_delete)} older ones.")

if __name__ == "__main__":
    main()
