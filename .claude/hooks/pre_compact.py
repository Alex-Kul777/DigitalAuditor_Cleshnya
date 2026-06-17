#!/usr/bin/env python3
"""PreCompact hook — saves context snapshot before compaction."""
import sys
import json
import os
from datetime import datetime

try:
    data = json.loads(sys.stdin.read())
    cwd = data.get("cwd", os.getcwd())
    tokens_used = data.get("context_size_tokens", 0)
    tokens_total = data.get("context_window_tokens", 80000)
    trigger = data.get("trigger", "unknown")

    mem_dir = os.path.join(cwd, ".claude", "memory")
    os.makedirs(mem_dir, exist_ok=True)
    snapshot_file = os.path.join(mem_dir, "compact_snapshot.md")

    pct = round(tokens_used / tokens_total * 100, 1) if tokens_total else 0
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    snapshot = f"""# Снимок перед компакцией — {timestamp}

- Токены: {tokens_used:,} / {tokens_total:,} ({pct}%)
- Триггер: {trigger}
"""

    with open(snapshot_file, "w") as f:
        f.write(snapshot)

    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "additionalContext": f"Компакция: {tokens_used:,}/{tokens_total:,} токенов ({pct}%). Снимок → .claude/memory/compact_snapshot.md"
        }
    }

    print(json.dumps(output))
    sys.exit(0)
except Exception as e:
    print(json.dumps({
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "additionalContext": f"Ошибка PreCompact hook: {str(e)}"
        }
    }))
    sys.exit(0)
