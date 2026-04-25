from pathlib import Path
from agents.cisa_auditor import CisaAuditor
from agents.uncle_robert import UncleRobertAgent
from knowledge.retriever import Retriever
from core.logger import setup_logger
from core.llm import get_llm
import json
import re
import os
import importlib
from datetime import datetime

class ReportOrchestrator:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.retriever = Retriever()
        self.logger = setup_logger("orchestrator")
        self.drafts_dir = task_dir / "drafts"
        self.drafts_dir.mkdir(exist_ok=True)
        self.config = self._load_config()

        # Initialize appropriate auditor based on config
        self.auditor = self._init_auditor()
    
    def _load_config(self) -> dict:
        import yaml
        config_path = self.task_dir / "config.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return {}

    def _init_auditor(self):
        """Initialize appropriate auditor based on config."""
        auditor_type = self.config.get("auditor", "cisa")

        if auditor_type == "uncle_robert":
            self.logger.info("Initializing UncleRobertAgent auditor")
            llm = get_llm(temperature=0.3)
            return UncleRobertAgent(llm, self.config)

        elif auditor_type == "cisa":
            self.logger.info("Initializing CisaAuditor")
            return CisaAuditor()

        else:
            self.logger.warning(f"Unknown auditor: {auditor_type}. Falling back to CISA.")
            return CisaAuditor()
    
    def _get_context(self, query: str, exclude_personas: list = None, task_name: str = None) -> str:
        """Retrieve relevant context from RAG with optional evidence filtering.

        Args:
            query: Search query
            exclude_personas: List of persona names to exclude (e.g., ['uncle_kahneman']).
                            If None, excludes all known personas by default (audit-only docs).
            task_name: Optional task identifier to filter evidence by task (M_Evidence feature)

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

            # Filter by task_name if provided (evidence isolation per task)
            filter_meta = {"task_name": task_name} if task_name else None

            docs = self.retriever.retrieve(query, k=5, exclude_personas=exclude_personas, filter=filter_meta)
            if docs:
                context = "\n\n".join([d["content"][:500] for d in docs])
                return context
        except Exception as e:
            self.logger.warning(f"RAG retrieval failed: {e}")
        return ""

    def _get_criteria_context(self, query: str) -> str:
        """Retrieve requirements context (L1/L2/L3) from RAG.

        Args:
            query: Search query for criteria/standards

        Returns:
            Criteria context string or empty string on failure
        """
        try:
            filter_meta = {"doc_type": {"$in": ["regulatory", "audit_standard", "local_policy"]}}
            docs = self.retriever.retrieve(query, k=8, exclude_personas=[], filter=filter_meta)
            if docs:
                context = "\n\n".join([d["content"][:300] for d in docs])
                return context
        except Exception as e:
            self.logger.warning(f"Criteria context retrieval failed: {e}")
        return ""

    def _build_findings_prompt(self, company: str, task_name: str) -> str:
        """Build findings prompt with evidence and criteria context.

        Args:
            company: Company name
            task_name: Task identifier for evidence filtering

        Returns:
            Enhanced findings prompt with context
        """
        sources = self.config.get('sources', [])
        sources_ctx = ", ".join(sources) if sources else company

        evidence_ctx = self._get_context(
            f"аудит {sources_ctx} нарушения проблемы риски",
            task_name=task_name
        )
        criteria_ctx = self._get_criteria_context(f"требования стандарты {sources_ctx}")

        prompt = f"""Ты — опытный аудитор CISA. Анализируй материалы о {sources_ctx}.

КОНТЕКСТ ИЗ ИСТОЧНИКА (Evidence):
{evidence_ctx or 'Контекст не найден — анализируй по общим принципам'}

ПРИМЕНИМЫЕ ТРЕБОВАНИЯ (L1/L2/L3):
{criteria_ctx or 'Требования не загружены — используй CISA/COBIT/ISO 27001'}

Сгенерируй 3-5 наблюдений в формате:

### Наблюдение [номер]: [заголовок]

**Состояние (Condition):** [описание текущей ситуации]

**Критерий (Criteria):** [ссылка на стандарт]

**Причина (Cause):** [корневая причина]

**Последствия (Impact):** [влияние на бизнес]

**Риск:** [High/Medium/Low]

**Рекомендация (Recommendation):** [конкретное действие]

**Срок устранения:** [разумный срок]

**Источники:**
| Тип | Документ | Стр. | Цитата |
|-----|----------|------|--------|
| Evidence | [имя файла] | [N] | "[цитата]" |
| L1 (Регулятор) | [файл] | [N] | "[текст требования]" |
| L2 (Аудит) | [файл] | [N] | "[текст стандарта]" |
| L3 (Локальный) | [файл или N/A] | [N] | "[текст или N/A]" |

КРИТИЧНО: Каждое наблюдение ДОЛЖНО содержать таблицу источников."""
        return prompt

    def _validate_citations(self, report_text: str) -> bool:
        """Validate presence of citation tables in findings.

        Args:
            report_text: Generated findings text

        Returns:
            True if 80%+ of findings have citations, False otherwise
        """
        findings_count = report_text.count("### Наблюдение")
        citations_count = len(re.findall(r"\| Evidence \|", report_text))

        if findings_count == 0:
            return True

        citation_ratio = citations_count / findings_count
        is_valid = citation_ratio >= 0.8

        if not is_valid:
            self.logger.warning(
                f"Citation validation: {citations_count}/{findings_count} findings "
                f"({citation_ratio*100:.0f}%) have citations (threshold: 80%)"
            )
        else:
            self.logger.info(f"Citation validation passed: {citation_ratio*100:.0f}%")

        return is_valid
    
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
        task_name = self.config.get('name', '')
        findings_prompt = self._build_findings_prompt(company, task_name)

        findings_text = self.auditor.generate_section(findings_prompt)

        # Validate citations in findings
        is_valid = self._validate_citations(findings_text)
        if not is_valid:
            self.logger.warning("Findings may lack proper citations — consider regenerating")

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

        # Reviewer hook: optionally inject reviewer comments
        self._apply_reviewer_hook(final_content)

        return output_path
    
    def _apply_reviewer_hook(self, final_content: str) -> None:
        """Apply reviewer comments to final report (optional, non-blocking).

        Checks config for 'reviewer' field. If set, loads reviewer class
        dynamically and calls review_markdown(). Saves reviewed report to
        separate file (Audit_Report_Reviewed.md).

        Args:
            final_content: Assembled final report markdown

        Note: Errors are logged but do NOT fail audit. Main Audit_Report.md
              is always saved to preserve audit trail.
        """
        # Check for reviewer override from CLI
        reviewer_name = os.getenv('DA_REVIEWER_OVERRIDE') or self.config.get('reviewer')

        if not reviewer_name:
            return  # No reviewer configured

        # Mapping of reviewer names to module paths
        REVIEWERS = {
            "uncle_kahneman": "agents.uncle_kahneman.UncleKahneman"
        }

        if reviewer_name not in REVIEWERS:
            self.logger.warning(f"Unknown reviewer '{reviewer_name}', skipping review")
            return

        try:
            # Dynamically load reviewer class
            module_path, class_name = REVIEWERS[reviewer_name].rsplit('.', 1)
            module = importlib.import_module(module_path)
            reviewer_class = getattr(module, class_name)

            self.logger.info(f"Applying {reviewer_name} review to report...")
            reviewer = reviewer_class(persona_name=reviewer_name)
            reviewed_content = reviewer.review_markdown(final_content)

            # Save reviewed report to separate file
            reviewed_path = self.task_dir / "output" / "Audit_Report_Reviewed.md"
            reviewed_path.write_text(reviewed_content, encoding='utf-8')

            self.logger.info(f"Reviewed report saved: {reviewed_path}")

        except Exception as e:
            self.logger.error(f"Reviewer '{reviewer_name}' failed: {e}", exc_info=True)
            # NOT re-raising — audit trail (Audit_Report.md) is already safe

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
