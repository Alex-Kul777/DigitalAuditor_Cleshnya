#!/usr/bin/env python3
"""Stop hook — writes session checkpoint marker to project_context.md and daily journal."""
import sys
import json
import os
import subprocess
from datetime import datetime

try:
    data = json.loads(sys.stdin.read())
    cwd = data.get("cwd", os.getcwd())
    mem_dir = os.path.join(cwd, ".claude", "memory")
    ctx_file = os.path.join(mem_dir, "project_context.md")

    os.makedirs(mem_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    marker = f"\n\n---\n_Сессия завершена: {timestamp}_\n"

    # Append marker to project_context.md; trim to 8000 chars rolling window
    if os.path.exists(ctx_file):
        with open(ctx_file) as f:
            content = f.read()
        content = (content + marker)[-8000:]
    else:
        content = f"# Контекст проекта DigitalAuditor_Cleshnya\n{marker}"

    with open(ctx_file, "w") as f:
        f.write(content)

    # === Daily journal ===
    journal_dir = os.path.join(mem_dir, "journal")
    os.makedirs(journal_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    session_time = datetime.now().strftime("%H:%M")
    journal_file = os.path.join(journal_dir, f"{today}.md")

    # Git commits since midnight
    try:
        commits = subprocess.check_output(
            ["git", "-C", cwd, "log", f"--since={today} 00:00",
             "--oneline", "--format=%h %s"],
            stderr=subprocess.DEVNULL, text=True, timeout=5
        ).strip() or "(нет коммитов)"
    except Exception:
        commits = "(git недоступен)"

    # Git status (uncommitted changes)
    try:
        status = subprocess.check_output(
            ["git", "-C", cwd, "status", "--short"],
            stderr=subprocess.DEVNULL, text=True, timeout=5
        ).strip() or "(чисто)"
    except Exception:
        status = "(git недоступен)"

    # Token info (from stdin if available)
    tokens_used = data.get("context_size_tokens", 0)
    tokens_total = data.get("context_window_tokens", 80000)
    token_pct = round(tokens_used / tokens_total * 100, 1) if tokens_total else 0

    entry = f"""
## Сессия {session_time}

### Коммиты за день
{commits}

### Незакоммиченные изменения
{status}

### Токены сессии
{tokens_used} / {tokens_total} ({token_pct}%)
"""

    # Create or append to today's journal
    if os.path.exists(journal_file):
        with open(journal_file, "a") as f:
            f.write(entry)
    else:
        with open(journal_file, "w") as f:
            f.write(f"# Журнал: {today}\n{entry}")

    sys.exit(0)
except Exception:
    # Silently fail — Stop hook doesn't output context
    sys.exit(0)
