#!/usr/bin/env python3
"""SessionStart hook — injects audit project context into Claude's session."""
import sys
import json
import os

try:
    data = json.loads(sys.stdin.read())
    cwd = data.get("cwd", os.getcwd())
    ctx_file = os.path.join(cwd, ".claude", "memory", "project_context.md")

    if os.path.exists(ctx_file):
        with open(ctx_file) as f:
            content = f.read().strip()
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": f"<audit-project-context>\n{content}\n</audit-project-context>"
            }
        }
    else:
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "<audit-project-context>НОВАЯ СЕССИЯ: project_context.md не создан. Создай .claude/memory/project_context.md после первой значимой работы.</audit-project-context>"
            }
        }

    print(json.dumps(output))
    sys.exit(0)
except Exception as e:
    print(json.dumps({
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": f"<audit-project-context>Ошибка SessionStart hook: {str(e)}</audit-project-context>"
        }
    }))
    sys.exit(0)
