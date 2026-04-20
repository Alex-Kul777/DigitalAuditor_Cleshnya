#!/usr/bin/env python3
"""
Запуск специализированного аудита Microsoft Copilot Chat
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from report_generator.orchestrator_ms import MSAuditOrchestrator

def main():
    task_dir = Path("tasks/instances/ms_copilot_audit")
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "output").mkdir(exist_ok=True)
    (task_dir / "drafts").mkdir(exist_ok=True)
    
    orchestrator = MSAuditOrchestrator(task_dir)
    report_path = orchestrator.generate_full_report()
    
    print(f"\n[+] Аудит завершен!")
    print(f"[+] Отчет сохранен: {report_path}")
    
    # Вывести краткую статистику
    print("\n=== Сводка аудита ===")
    print(f"Задач аудита: {len(orchestrator.scope.get('audit_tasks', []))}")
    print(f"Учтено в SWOT: S={len(orchestrator.scope.get('swot_analysis', {}).get('strengths', []))}, W={len(orchestrator.scope.get('swot_analysis', {}).get('weaknesses', []))}")
    print("=====================")

if __name__ == "__main__":
    main()
