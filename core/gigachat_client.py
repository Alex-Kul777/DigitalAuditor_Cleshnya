import time
import os
from typing import Optional, Any
from core.logger import setup_logger
from core.token_counter import TokenCounter

logger = setup_logger("gigachat_client")


class GigaChatClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, max_retries: int = 3, timeout: int = 60, scope: Optional[str] = None):
        self.api_key = api_key or os.getenv("GIGACHAT_API_KEY")
        self.model = model or os.getenv("GIGACHAT_MODEL", "GigaChat-2-Max")
        self.scope = scope or os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_B2B")
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
                from gigachat import GigaChat as GigaChatSDK
                from gigachat.models import Chat, Messages, MessagesRole

                client = GigaChatSDK(
                    credentials=self.api_key,
                    scope=self.scope,
                    model=self.model,
                    verify_ssl_certs=False,
                    timeout=self.timeout
                )

                messages = [
                    Messages(role=MessagesRole.SYSTEM, content="Ты — старший ИТ-аудитор с сертификатами CISA и CIA."),
                    Messages(role=MessagesRole.USER, content=prompt)
                ]

                self.token_counter.add_prompt(prompt)
                response = client.chat(Chat(messages=messages))
                response_text = response.choices[0].message.content

                self.token_counter.add_completion(response_text)
                self._record_success()

                return response_text

            except ImportError:
                logger.warning("gigachat SDK not installed. Run: pip install gigachat")
                return None
            except Exception as e:
                logger.warning(f"GigaChat attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    self._record_failure()

        return None

    def get_token_usage(self):
        return self.token_counter.get_usage()
