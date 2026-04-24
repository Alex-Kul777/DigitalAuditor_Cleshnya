from pathlib import Path
from agents.cisa_auditor import CisaAuditor
from knowledge.retriever import Retriever
from core.logger import setup_logger
import json
from datetime import datetime

class ReportOrchestrator:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.auditor = CisaAuditor()
        self.retriever = Retriever()
        self.logger = setup_logger("orchestrator")
        self.drafts_dir = task_dir / "drafts"
        self.drafts_dir.mkdir(exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        import yaml
        config_path = self.task_dir / "config.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return {}
    
    def _get_context(self, query: str, exclude_personas: list = None) -> str:
        """Получить релевантный контекст из RAG.

        Args:
            query: Search query
            exclude_personas: List of persona names to exclude (e.g., ['uncle_kahneman']).
                            If None, excludes all known personas by default (audit-only docs).

        Returns:
            Context string from retrieved documents or empty string on failure
        """
        try:
            # If not specified, exclude all personas (pure audit context)
            if exclude_personas is None:
                from knowledge.persona_indexer import PersonaIndexer
                persona_indexer = PersonaIndexer()
                exclude_personas = persona_indexer.list_personas()
                self.logger.debug(f"Excluding personas: {exclude_personas}")

            docs = self.retriever.retrieve(query, k=3, exclude_personas=exclude_personas)
            if docs:
                context = "\n\n".join([d["content"][:500] for d in docs])
                return context
        except Exception as e:
            self.logger.warning(f"RAG retrieval failed: {e}")
        return ""
    
    def generate(self, findings: list = None) -> Path:
        self.logger.info("Starting report generation")
        
        company = self.config.get('company', 'Не указана')
        audit_type = self.config.get('audit_type', 'IT')
        
        # Глава 1: Executive Summary
        self.logger.info("Generating Executive Summary...")
        exec_prompt = f"""Составь Executive Summary для отчета об ИТ-аудите компании "{company}".
Включи:
1. Краткое описание объекта аудита
2. Ключевые выводы (3-5 пунктов)
3. Общую оценку контрольной среды
4. Топ-3 критических риска

Объем: 3-4 абзаца. Отвечай на русском языке в официально-деловом стиле."""
        
        exec_summary = self.auditor.generate_section(exec_prompt)
        (self.drafts_dir / "01_executive_summary.md").write_text(exec_summary, encoding='utf-8')
        
        # Глава 2: Цели и объем
        self.logger.info("Generating Scope...")
        scope_prompt = f"""Опиши цели и объем ИТ-аудита компании "{company}".
Укажи:
- Период аудита
- Проверяемые системы и процессы
- Применяемые стандарты (CISA, COBIT, ISO 27001)
- Ограничения аудита

Объем: 2-3 абзаца."""
        
        scope = self.auditor.generate_section(scope_prompt)
        (self.drafts_dir / "02_scope.md").write_text(scope, encoding='utf-8')
        
        # Глава 3: Методология
        self.logger.info("Generating Methodology...")
        
        # Пытаемся получить контекст из RAG
        rag_context = self._get_context("методология ИТ аудита CISA цифровые инструменты")
        
        method_prompt = f"""Опиши методологию проведения ИТ-аудита.
{f'Используй следующую информацию из базы знаний:\n{rag_context}' if rag_context else ''}

Включи:
- Использованные стандарты и фреймворки
- Инструменты анализа данных (Python, SQL, RAG)
- Процедуры сбора доказательств
- Методы оценки рисков

Объем: 2-3 абзаца со ссылками на стандарты."""
        
        methodology = self.auditor.generate_section(method_prompt)
        (self.drafts_dir / "03_methodology.md").write_text(methodology, encoding='utf-8')
        
        # Глава 4: Наблюдения
        self.logger.info("Generating Findings...")
        findings_prompt = f"""Сгенерируй 3 типичных наблюдения для ИТ-аудита компании "{company}".
Для каждого наблюдения используй формат:

### Наблюдение [номер]: [заголовок]

**Состояние (Condition):**
[описание текущей ситуации]

**Критерий (Criteria):**
[ссылка на стандарт CISA или нормативный документ]

**Причина (Cause):**
[корневая причина]

**Последствия (Impact):**
[влияние на бизнес]

**Риск:** [High/Medium/Low]

**Рекомендация (Recommendation):**
[конкретное действие]

**Срок устранения:** [разумный срок]

Разделяй наблюдения пустой строкой."""
        
        findings_text = self.auditor.generate_section(findings_prompt)
        (self.drafts_dir / "04_findings.md").write_text(findings_text, encoding='utf-8')
        
        # Глава 5: Заключение
        self.logger.info("Generating Conclusion...")
        conclusion_prompt = f"""Напиши заключение для отчета об ИТ-аудите компании "{company}".
Включи:
- Общую оценку состояния ИТ-контролей
- Ключевые рекомендации для руководства
- План последующих действий

Объем: 2-3 абзаца."""
        
        conclusion = self.auditor.generate_section(conclusion_prompt)
        (self.drafts_dir / "05_conclusion.md").write_text(conclusion, encoding='utf-8')
        
        # Сборка итогового отчета
        self.logger.info("Assembling final report...")
        final_content = self._assemble_report(company)
        
        output_path = self.task_dir / "output" / "Audit_Report.md"
        output_path.write_text(final_content, encoding='utf-8')
        
        self.logger.info(f"Report saved to {output_path}")
        return output_path
    
    def _assemble_report(self, company: str) -> str:
        chapters = [
            f"# Отчет об ИТ-аудите\n\n**Компания:** {company}\n**Дата:** {datetime.now().strftime('%d.%m.%Y')}\n\n---\n\n",
            "## 1. Резюме для руководства (Executive Summary)\n\n",
            (self.drafts_dir / "01_executive_summary.md").read_text(encoding='utf-8'),
            "\n\n---\n\n## 2. Цели и объем аудита\n\n",
            (self.drafts_dir / "02_scope.md").read_text(encoding='utf-8'),
            "\n\n---\n\n## 3. Методология\n\n",
            (self.drafts_dir / "03_methodology.md").read_text(encoding='utf-8'),
            "\n\n---\n\n## 4. Детальные наблюдения\n\n",
            (self.drafts_dir / "04_findings.md").read_text(encoding='utf-8'),
            "\n\n---\n\n## 5. Заключение\n\n",
            (self.drafts_dir / "05_conclusion.md").read_text(encoding='utf-8'),
        ]
        return "".join(chapters)
