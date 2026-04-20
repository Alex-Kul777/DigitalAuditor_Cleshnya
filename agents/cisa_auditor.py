from agents.base import BaseAgent
from langchain_ollama import OllamaLLM
from core.config import OLLAMA_BASE_URL, OLLAMA_MODEL

SYSTEM_PROMPT = """Ты — старший ИТ-аудитор с сертификатами CISA и CIA.
Твоя задача — проводить аудит в соответствии с международными стандартами.
Отвечай на русском языке в официально-деловом стиле.
Обязательно ссылайся на источники и стандарты."""

class CisaAuditor(BaseAgent):
    def __init__(self):
        super().__init__("cisa_auditor")
        # Используем обновленный импорт
        self.llm = OllamaLLM(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=0.3,
            num_ctx=8192,
        )
    
    def execute(self, task: str) -> str:
        prompt = f"{SYSTEM_PROMPT}\n\nЗадача: {task}"
        return self.llm.invoke(prompt)
    
    def generate_section(self, prompt: str) -> str:
        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
        return self.llm.invoke(full_prompt)
