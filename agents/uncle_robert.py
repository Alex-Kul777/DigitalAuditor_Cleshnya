"""Uncle Robert — IIA-compliant auditor using Brink's Modern Internal Auditing framework."""
import re
from agents.base import BaseAgent
from report_generator.ccce_formatter import CCCEFormatter
from knowledge.retriever import Retriever
from core.logger import setup_logger


class UncleRobertAgent(BaseAgent):
    """IIA-compliant auditor using Brink's framework and CCCE findings format."""

    def __init__(self, llm, config):
        """Initialize UncleRobertAgent with LLM and configuration."""
        super().__init__(llm)
        self.config = config
        self.retriever = Retriever()
        self.ccce_formatter = CCCEFormatter()
        self.logger = setup_logger("UncleRobertAgent")

    def execute(self, task):
        """Execute audit using two-stage pipeline: Draft → Final."""
        self.logger.info(f"Starting uncle_robert audit: {task.task_name}")

        # Stage 1: Preliminary Findings Point Sheet
        draft_findings = self._generate_draft_findings(task)

        # Stage 2: Management Review & Final Report
        final_findings = self._incorporate_management_response(draft_findings)

        return final_findings

    def _generate_draft_findings(self, task):
        """Generate preliminary observations (Stage 1)."""
        context = self._get_audit_context(task)

        prompt = self._build_draft_findings_prompt(task, context)
        draft_text = self.llm.invoke(prompt)

        # Parse into CCCE observations
        observations = self._parse_ccce_observations(draft_text)
        return observations

    def _get_audit_context(self, task):
        """Retrieve Brink's guidance for audit procedures and standards."""
        queries = [
            "audit evidence sampling procedures",
            "IIA professional practice standards",
            "control weaknesses documentation",
            "audit finding format and elements"
        ]

        context_parts = []
        for q in queries:
            try:
                docs = self.retriever.retrieve(
                    q, k=3,
                    filter={"authority": "Brink", "req_level": 2}
                )
                context_parts.extend([d.page_content for d in docs])
            except Exception as e:
                self.logger.warning(f"Failed to retrieve context for '{q}': {e}")

        return "\n\n".join(context_parts) if context_parts else "Brink's guidance not available (PDF not indexed yet)"

    def _build_draft_findings_prompt(self, task, brinks_context):
        """Construct prompt that enforces CCCE structure."""
        evidence_context = getattr(task, 'evidence_context', 'No evidence provided')
        requirements_context = getattr(task, 'requirements_context', 'No requirements provided')
        company = task.config.get('company', 'Unknown')

        return f"""Ты Uncle Robert — опытный аудитор по стандартам IIA и Brink's Modern Internal Auditing.

КОНТЕКСТ ИЗ БРИНКСА (Глава 8: IIA стандарты; Глава 17: формат наблюдений):
{brinks_context}

ЗАДАЧА АУДИТА: {task.task_name} ({company})

ИСТОЧНИКИ (Evidence):
{evidence_context}

ТРЕБОВАНИЯ (L1/L2/L3):
{requirements_context}

Сгенерируй 3-5 ПРЕДВАРИТЕЛЬНЫХ наблюдений (draft findings point sheet).

ДЛЯ КАЖДОГО наблюдения ОБЯЗАТЕЛЬНО:
1. **Condition** (факт из аудита)
   - Что обнаружено, тест-результат, документ
   - Ссылка на программу аудита и рабочие листы

2. **Criteria** (какой стандарт нарушен)
   - L1 (Регулятор): ФСТЭК/GDPR/ФЗ-152
   - L2 (Аудит): IIA/CISA/COBIT/ISO + Brink's глава
   - L3 (Локальный): политика аудитируемого

3. **Cause** (корневая причина)
   - НЕ симптом, а ПОЧЕМУ (отсутствие процедуры, gap в обучении)

4. **Effect** (последствие/риск)
   - Деловое последствие: финансовое, compliance, операционное
   - Квантифицировать если возможно

5. **Risk Rating**: High/Medium/Low

Формат каждого наблюдения:
```
### Observation N: [Заголовок]

**Condition:**
[Что обнаружено + тест-результат + ссылка на программу]

**Criteria:**
- L1: [текст требования]
- L2: Brink's Chapter 8, IIA Standard [X]: [текст]
- L3: [политика аудитируемого]

**Cause:**
[Корневая причина, не симптом]

**Effect:**
[Деловое последствие + риск-рейтинг]

**Preliminary Recommendation:**
[Действие для исправления]
```

ВАЖНО: Это DRAFT findings point sheet для обсуждения с менеджментом (Brink's Exhibit 15.4).
Не добавляй окончательные выводы аудитора до получения ответа менеджмента."""

    def _parse_ccce_observations(self, draft_text):
        """Parse LLM output into structured CCCE observations."""
        observations = []

        # Split by "### Observation" pattern
        obs_pattern = r'### Observation \d+:\s*(.+?)(?=### Observation|\Z)'
        matches = re.finditer(obs_pattern, draft_text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            obs_block = match.group(0)
            obs_title = match.group(1).strip()

            # Extract CCCE sections
            condition = self._extract_section(obs_block, 'Condition')
            criteria = self._extract_section(obs_block, 'Criteria')
            cause = self._extract_section(obs_block, 'Cause')
            effect = self._extract_section(obs_block, 'Effect')
            risk_rating = self._extract_section(obs_block, 'Risk Rating')
            recommendation = self._extract_section(obs_block, 'Preliminary Recommendation')

            observation = {
                'title': obs_title,
                'condition': condition,
                'criteria': criteria,
                'cause': cause,
                'effect': effect,
                'risk_rating': risk_rating or 'Medium',
                'recommendation': recommendation,
            }
            observations.append(observation)

        return observations

    @staticmethod
    def _extract_section(text, section_name):
        """Extract a named section from observation text."""
        pattern = rf'\*\*{section_name}:\*\*\s*(.+?)(?=\*\*\w+:|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _incorporate_management_response(self, draft_findings):
        """Finalize findings after management response (Stage 2)."""
        # Placeholder: in full implementation, would prompt for mgmt response
        # For MVP, return draft findings as-is
        self.logger.info(f"Finalizing {len(draft_findings)} findings after management review")
        return draft_findings

    def generate_section(self, section_name):
        """Generate specific report section (override BaseAgent)."""
        if section_name == "findings":
            return self._format_final_findings()
        return super().generate_section(section_name)

    def _format_final_findings(self):
        """Format findings into final report structure."""
        # Placeholder: would use self.ccce_formatter to convert observations
        return "## Findings\n(Findings would be formatted here)"
