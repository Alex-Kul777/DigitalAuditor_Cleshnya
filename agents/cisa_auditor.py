from agents.base import BaseAgent
from core.llm import get_llm
from core.logger import setup_logger

logger = setup_logger("agents.cisa_auditor")

SYSTEM_PROMPT = """Ты — старший ИТ-аудитор с сертификатами CISA и CIA.
Твоя задача — проводить аудит в соответствии с международными стандартами.
Отвечай на русском языке в официально-деловом стиле.
Обязательно ссылайся на источники и стандарты."""


class CisaAuditor(BaseAgent):
    def __init__(self):
        super().__init__("cisa_auditor")
        self.llm = get_llm(temperature=0.3)

    def execute(self, task: str) -> str:
        prompt = f"{SYSTEM_PROMPT}\n\nЗадача: {task}"
        logger.info(f"CisaAuditor executing task (prompt length: {len(prompt)})")
        result = self.llm.invoke(prompt)
        logger.info(f"CisaAuditor task complete (response length: {len(result)})")
        return result

    def generate_section(self, prompt: str) -> str:
        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
        logger.info(f"Generating section (prompt length: {len(full_prompt)})")
        result = self.llm.invoke(full_prompt)
        logger.info(f"Section generated (response length: {len(result)})")
        return result
