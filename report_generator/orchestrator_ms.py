"""
Специализированный оркестратор для аудита Microsoft Copilot Chat
Учитывает конкретные задачи аудита и SWOT-анализ
"""

from pathlib import Path
import yaml
from agents.cisa_auditor import CisaAuditor
from knowledge.retriever import Retriever
from core.logger import setup_logger

class MSAuditOrchestrator:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.auditor = CisaAuditor()
        self.retriever = Retriever()
        self.logger = setup_logger("ms_audit")
        self.drafts_dir = task_dir / "drafts"
        self.drafts_dir.mkdir(exist_ok=True)
        self.scope = self._load_scope()
        
    def _load_scope(self):
        scope_file = self.task_dir / "audit_scope.yaml"
        if scope_file.exists():
            return yaml.safe_load(scope_file.read_text(encoding='utf-8'))
        return {}
    
    def generate_task_finding(self, task: dict, index: int) -> str:
        """Сгенерировать наблюдение по конкретной задаче аудита"""
        
        # Поиск релевантного контекста в коде
        context = ""
        for query in task.get('rag_queries', []):
            docs = self.retriever.retrieve(query, k=3)
            if docs:
                context += "\n\n".join([d['content'][:500] for d in docs])
        
        prompt = f"""
Ты проводишь аудит репозитория GitHub Copilot Chat.
Задача аудита: {task['name']}
Описание: {task['description']}
Применимые стандарты: {', '.join(task.get('standards', []))}

Найденный контекст из кода:
{context[:2000] if context else 'Контекст не найден'}

Сгенерируй наблюдение аудита в формате:

### Наблюдение {index}: {task['name']}

**Состояние (Condition):**
[опиши текущую ситуацию в коде]

**Критерий (Criteria):**
[укажи конкретный стандарт и пункт]

**Причина (Cause):**
[почему ситуация требует внимания]

**Последствия (Impact):**
[влияние на безопасность или качество]

**Риск:** [High/Medium/Low]

**Рекомендация (Recommendation):**
[конкретное улучшение]

**Ссылка на код:** [файл и строка, если найдены]
"""
        return self.auditor.generate_section(prompt)
    
    def generate_swot_section(self) -> str:
        """Сгенерировать раздел SWOT-анализа для отчета"""
        swot = self.scope.get('swot_analysis', {})
        
        prompt = f"""
На основе следующего SWOT-анализа возможностей ИИ-аудитора, 
составь раздел "Оценка методологии аудита" для итогового отчета:

Сильные стороны:
{chr(10).join('- ' + s for s in swot.get('strengths', []))}

Слабые стороны:
{chr(10).join('- ' + s for s in swot.get('weaknesses', []))}

Возможности:
{chr(10).join('- ' + s for s in swot.get('opportunities', []))}

Угрозы:
{chr(10).join('- ' + s for s in swot.get('threats', []))}

Напиши профессиональный раздел на русском языке объемом 2-3 абзаца.
"""
        return self.auditor.generate_section(prompt)
    
    def generate_full_report(self):
        """Генерация полного отчета с учетом всех задач"""
        
        self.logger.info("Starting Microsoft Copilot Chat audit")
        
        # 1. Резюме
        exec_prompt = f"""
Составь Executive Summary для аудита GitHub Copilot Chat.
Цель: {self.scope.get('audit_objectives', {}).get('primary', '')}
Объем: 3-4 абзаца, русский язык, деловой стиль.
"""
        executive = self.auditor.generate_section(exec_prompt)
        (self.drafts_dir / "01_executive.md").write_text(executive, encoding='utf-8')
        
        # 2. SWOT-анализ методологии
        swot_section = self.generate_swot_section()
        (self.drafts_dir / "02_swot_methodology.md").write_text(swot_section, encoding='utf-8')
        
        # 3. Генерация наблюдений по каждой задаче
        findings = []
        for i, task in enumerate(self.scope.get('audit_tasks', []), 1):
            self.logger.info(f"Processing task: {task['id']}")
            finding = self.generate_task_finding(task, i)
            findings.append(finding)
            (self.drafts_dir / f"03_finding_{task['id']}.md").write_text(finding, encoding='utf-8')
        
        # 4. Заключение с учетом SWOT
        conclusion_prompt = f"""
Составь заключение аудита GitHub Copilot Chat.
Учитывай следующие угрозы и ограничения методологии:
{chr(10).join('- ' + t for t in self.scope.get('swot_analysis', {}).get('threats', []))}

Напиши 2-3 абзаца на русском языке.
"""
        conclusion = self.auditor.generate_section(conclusion_prompt)
        (self.drafts_dir / "04_conclusion.md").write_text(conclusion, encoding='utf-8')
        
        # 5. Сборка отчета
        report = []
        report.append("# Отчет об ИТ-аудите\n\n")
        report.append(f"**Объект:** GitHub Copilot Chat (Microsoft)\n")
        report.append(f"**Цель:** {self.scope.get('audit_objectives', {}).get('primary', '')}\n\n---\n\n")
        report.append("## 1. Резюме для руководства\n\n")
        report.append(executive)
        report.append("\n\n---\n\n## 2. Оценка методологии аудита (SWOT)\n\n")
        report.append(swot_section)
        report.append("\n\n---\n\n## 3. Детальные наблюдения\n\n")
        report.append("\n\n".join(findings))
        report.append("\n\n---\n\n## 4. Заключение\n\n")
        report.append(conclusion)
        
        output_path = self.task_dir / "output" / "MS_Copilot_Audit_Report.md"
        output_path.write_text("".join(report), encoding='utf-8')
        
        self.logger.info(f"Report saved to {output_path}")
        return output_path
