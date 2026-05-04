#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime

def generate_prompt():
    project_root = Path(__file__).parent.parent
    prompts_dir = project_root / "prompts"
    prompts_dir.mkdir(exist_ok=True)

    output_file = prompts_dir / "claude_gigachat_integration.md"

    date_str = datetime.now().strftime("%d.%m.%Y")

    content = '''# Инструкция для Claude: Интеграция GigaChat в DigitalAuditor Cleshnya

**Дата:** ''' + date_str + '''
**Версия:** 1.0

---

## Контекст

Ты выполняешь интеграцию GigaChat API в проект DigitalAuditor Cleshnya на основе лучших практик из проекта rag_GigaChat.

**Исходный проект:** https://github.com/Alex-Kul777/rag_GigaChat
**Целевой проект:** https://github.com/Alex-Kul777/DigitalAuditor_Cleshnya

**Принятые решения:**
- Приоритет провайдеров: GigaChat → Ollama → Claude → OpenAI
- Средний уровень интеграции: token_counter + валидация
- Продвинутая обработка ошибок: retry + circuit breaker
- Модель GigaChat настраивается через GIGACHAT_MODEL
- Проверка API при старте
- langchain-gigachat как опциональная зависимость

---

## Шаг 1: Создать requirements-gigachat.txt

Файл: `requirements-gigachat.txt`

```text
langchain-gigachat>=0.1.0
```

---

## Шаг 2: Обновить .env.example

Файл: `.env.example`

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=digital-auditor-cisa

LLM_PROVIDER=hybrid
GIGACHAT_API_KEY=your_gigachat_key_here
GIGACHAT_MODEL=GigaChat-2-Max
GIGACHAT_MAX_TOKENS=2000
GIGACHAT_TIMEOUT=60
GIGACHAT_MAX_RETRIES=3

ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

TAVILY_API_KEY=your_tavily_key_here

LOG_LEVEL=INFO
LOG_FILE=audit.log
```

---

## Шаг 3: Создать core/token_counter.py

Файл: `core/token_counter.py`

```python
import tiktoken
from dataclasses import dataclass
from typing import Optional

@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class TokenCounter:
    def __init__(self, model_name: str = "gpt-4o"):
        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        self.usage = TokenUsage()

    def count(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def add_prompt(self, text: str):
        tokens = self.count(text)
        self.usage.prompt_tokens += tokens
        self.usage.total_tokens += tokens
        return tokens

    def add_completion(self, text: str):
        tokens = self.count(text)
        self.usage.completion_tokens += tokens
        self.usage.total_tokens += tokens
        return tokens

    def reset(self):
        self.usage = TokenUsage()

    def get_usage(self) -> TokenUsage:
        return self.usage
```

---

## Шаг 4: Создать core/gigachat_validator.py

Файл: `core/gigachat_validator.py`

```python
import os
import requests
from typing import Optional
from core.logger import setup_logger

logger = setup_logger("gigachat_validator")

class GigaChatValidator:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key or os.getenv("GIGACHAT_API_KEY")
        self.timeout = timeout
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"

    def validate_api_key(self) -> bool:
        if not self.api_key:
            logger.warning("GIGACHAT_API_KEY is not set")
            return False
        return True

    def check_connection(self) -> bool:
        if not self.validate_api_key():
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=self.timeout
            )
            if response.status_code == 200:
                logger.info("GigaChat API connection successful")
                return True
            else:
                logger.warning(f"GigaChat API returned status {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            logger.warning("GigaChat API connection timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("GigaChat API connection error")
            return False
        except Exception as e:
            logger.debug(f"GigaChat API check failed: {e}", exc_info=True)
            return False

    def is_available(self) -> bool:
        return self.check_connection()
```

---

## Шаг 5: Создать core/gigachat_client.py

Файл: `core/gigachat_client.py`

```python
import time
import os
from typing import Optional, Any
from core.logger import setup_logger
from core.token_counter import TokenCounter

logger = setup_logger("gigachat_client")

class GigaChatClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, max_retries: int = 3, timeout: int = 60):
        self.api_key = api_key or os.getenv("GIGACHAT_API_KEY")
        self.model = model or os.getenv("GIGACHAT_MODEL", "GigaChat-2-Max")
        self.max_retries = max_retries
        self.timeout = timeout
        self.token_counter = TokenCounter()
        self._failure_count = 0
        self._circuit_open = False
        self._last_failure_time = 0
        self._circuit_reset_timeout = 60

    def _is_circuit_open(self) -> bool:
        if self._circuit_open:
            if time.time() - self._last_failure_time > self._circuit_reset_timeout:
                self._circuit_open = False
                self._failure_count = 0
                logger.info("Circuit breaker reset")
            else:
                return True
        return False

    def _record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.max_retries:
            self._circuit_open = True
            logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    def _record_success(self):
        self._failure_count = 0
        self._circuit_open = False

    def invoke(self, prompt: str) -> Optional[str]:
        if self._is_circuit_open():
            logger.warning("Circuit breaker is open, skipping GigaChat")
            return None

        for attempt in range(self.max_retries):
            try:
                from langchain_gigachat import GigaChat

                llm = GigaChat(
                    api_key=self.api_key,
                    model=self.model,
                    timeout=self.timeout,
                    max_tokens=int(os.getenv("GIGACHAT_MAX_TOKENS", "2000")),
                    temperature=0.3,
                    verbose=False
                )

                self.token_counter.add_prompt(prompt)
                response = llm.invoke(prompt)
                self.token_counter.add_completion(response)
                self._record_success()

                return response

            except ImportError:
                logger.warning("langchain_gigachat not installed")
                return None
            except Exception as e:
                logger.warning(f"GigaChat attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    self._record_failure()

        return None

    def get_token_usage(self):
        return self.token_counter.get_usage()
```

---

## Шаг 6: Обновить core/llm.py

Файл: `core/llm.py`

```python
import os
from core.logger import setup_logger
from core.gigachat_validator import GigaChatValidator
from core.gigachat_client import GigaChatClient

logger = setup_logger("llm")


class GigaChatWrapper:
    """Wrapper for GigaChat to match BaseLLM interface."""
    def __init__(self, api_key: str, model: str, temperature: float = 0.3, timeout: int = 60, max_retries: int = 3):
        self.client = GigaChatClient(api_key=api_key, model=model, max_retries=max_retries, timeout=timeout)
        self.temperature = temperature

    def invoke(self, prompt: str) -> str:
        response = self.client.invoke(prompt)
        if response is None:
            raise RuntimeError("GigaChat failed and no fallback available")
        return response

    def get_type(self) -> str:
        return "gigachat-wrapper"


class LLMFactory:
    _gigachat_client = None
    _gigachat_available = None

    @classmethod
    def _check_gigachat(cls) -> bool:
        if cls._gigachat_available is None:
            validator = GigaChatValidator()
            cls._gigachat_available = validator.is_available()
            if cls._gigachat_available:
                logger.info("GigaChat is available")
            else:
                logger.info("GigaChat is not available")
        return cls._gigachat_available

    @classmethod
    def get_llm(cls, temperature: float = 0.3):
        provider = os.getenv("LLM_PROVIDER", "hybrid").lower()

        if provider == "hybrid":
            if cls._check_gigachat():
                provider = "gigachat"
            else:
                provider = "ollama"

        logger.info(f"Selected LLM provider: {provider}")

        if provider == "gigachat":
            return cls._get_gigachat(temperature)
        elif provider == "anthropic":
            return cls._get_anthropic(temperature)
        elif provider == "openai":
            return cls._get_openai(temperature)
        else:
            return cls._get_ollama(temperature)

    @classmethod
    def _get_gigachat(cls, temperature: float):
        wrapper = GigaChatWrapper(
            api_key=os.getenv("GIGACHAT_API_KEY"),
            model=os.getenv("GIGACHAT_MODEL", "GigaChat-2-Max"),
            temperature=temperature,
            timeout=int(os.getenv("GIGACHAT_TIMEOUT", "60")),
            max_retries=int(os.getenv("GIGACHAT_MAX_RETRIES", "3"))
        )

        def invoke_with_fallback(prompt: str) -> str:
            try:
                return wrapper.invoke(prompt)
            except Exception as e:
                logger.info(f"GigaChat failed: {e}, falling back to Ollama")
                ollama_llm = cls._get_ollama(temperature)
                return ollama_llm.invoke(prompt)

        from langchain_core.language_models.llms import BaseLLM
        from langchain_core.callbacks import CallbackManagerForLLMRun
        from typing import Optional, List, Any
        from langchain_core.outputs import LLMResult, Generation

        class GigaChatLLMAdapter(BaseLLM):
            temperature: float = temperature

            def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> Any:
                generations = []
                for prompt in prompts:
                    text = invoke_with_fallback(prompt)
                    generations.append([Generation(text=text)])
                return LLMResult(generations=generations)

            def _llm_type(self) -> str:
                return "gigachat-adapter"

        return GigaChatLLMAdapter()

    @classmethod
    def _get_ollama(cls, temperature: float):
        from langchain_ollama import OllamaLLM
        return OllamaLLM(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "digital-auditor-cisa"),
            temperature=temperature,
            num_ctx=8192
        )

    @classmethod
    def _get_anthropic(cls, temperature: float):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    @classmethod
    def _get_openai(cls, temperature: float):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o",
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )


def get_llm(temperature: float = 0.3):
    return LLMFactory.get_llm(temperature)
```

---

## Шаг 7: Обновить agents/cisa_auditor.py

Файл: `agents/cisa_auditor.py`

```python
from agents.base import BaseAgent
from core.llm import get_llm

SYSTEM_PROMPT = """Ты — старший ИТ-аудитор с сертификатами CISA и CIA.
Твоя задача — проводить аудит в соответствии с международными стандартами.
Отвечай на русском языке в официально-деловом стиле.
Обязательно ссылайся на источники и стандарты."""

class CisaAuditor(BaseAgent):
    def __init__(self):
        super().__init__("cisa_auditor")
        self.llm = get_llm(temperature=0.3)

    def execute(self, task: str) -> str:
        prompt = f"{SYSTEM_PROMPT}\\n\\nЗадача: {task}"
        return self.llm.invoke(prompt)

    def generate_section(self, prompt: str) -> str:
        full_prompt = f"{SYSTEM_PROMPT}\\n\\n{prompt}"
        return self.llm.invoke(full_prompt)
```

---

## Шаг 8: Обновить core/config.py

Файл: `core/config.py`

Добавить GigaChat переменные в конфиг и к легасси экспортам:

```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "hybrid")
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY", "")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat-2-Max")
GIGACHAT_MAX_TOKENS = int(os.getenv("GIGACHAT_MAX_TOKENS", "2000"))
GIGACHAT_TIMEOUT = int(os.getenv("GIGACHAT_TIMEOUT", "60"))
GIGACHAT_MAX_RETRIES = int(os.getenv("GIGACHAT_MAX_RETRIES", "3"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
```

---

## Шаг 9: Добавить tiktoken в requirements.txt

Добавить строку: `tiktoken>=0.5.0`
Добавить строку: `langchain-ollama>=0.1.0`
Добавить строку: `langchain-openai>=0.2.0`
Добавить строку: `langchain-anthropic>=0.1.0`

---

## Шаг 10: Порядок выполнения

1. Создай все файлы согласно шагам 1-9
2. Установи зависимости: `pip install -r requirements.txt`
3. Установи опциональную зависимость: `pip install -r requirements-gigachat.txt`
4. Добавь GIGACHAT_API_KEY в .env
5. Запусти тест: `python -c "from core.llm import get_llm; llm = get_llm(); print(llm)"`
6. Проверь логи: должен показать выбранный провайдер

---

## Шаг 11: Проверка fallback

1. Временно удали GIGACHAT_API_KEY из .env
2. Запусти тест снова
3. Должен автоматически переключиться на Ollama
4. Верни ключ обратно

---

## Шаг 12: Проверка полного цикла аудита

```bash
python main.py create --name test_gigachat --company "Тест" --sources "тест"
python main.py run --task test_gigachat
```

Убедись что аудит выполняется с GigaChat и отчёт генерируется корректно.
'''

    output_file.write_text(content, encoding='utf-8')
    print(f"[+] Instruction created: {output_file}")
    print(f"[+] File size: {len(content)} characters")


if __name__ == "__main__":
    generate_prompt()
