import time
import os
from typing import Optional, Any
from core.logger import setup_logger
from core.token_counter import TokenCounter

logger = setup_logger("gigachat_client")


class GigaChatClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, max_retries: int = 3, timeout: int = 60, scope: Optional[str] = None, context_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("GIGACHAT_API_KEY")
        self.model = model or os.getenv("GIGACHAT_MODEL", "GigaChat-2-Max")
        self.scope = scope or os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_B2B")
        self.max_retries = max_retries
        self.timeout = timeout
        self.token_counter = TokenCounter()
        self.context_id = context_id
        self._failure_count = 0
        self._circuit_open = False
        self._last_failure_time = 0
        self._circuit_reset_timeout = 60
        # Metrics tracking
        self._metrics = {
            "attempt_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "last_error": None,
            "circuit_breaker_status": "closed",
            "first_attempt_time": None,
            "last_attempt_time": None
        }

    def _is_circuit_open(self) -> bool:
        if self._circuit_open:
            if time.time() - self._last_failure_time > self._circuit_reset_timeout:
                self._circuit_open = False
                self._failure_count = 0
                self._metrics["circuit_breaker_status"] = "closed"
                logger.structured_log(
                    "circuit_breaker", "reset",
                    {
                        "context_id": self.context_id,
                        "reset_after_ms": int(self._circuit_reset_timeout * 1000)
                    },
                    level="INFO"
                )
            else:
                return True
        return False

    def _record_failure(self, error: str = None):
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._metrics["failure_count"] += 1
        self._metrics["last_error"] = error
        self._metrics["last_attempt_time"] = time.time()
        if self._failure_count >= self.max_retries:
            self._circuit_open = True
            self._metrics["circuit_breaker_status"] = "open"
            logger.structured_log(
                "circuit_breaker", "opened",
                {
                    "context_id": self.context_id,
                    "failure_count": self._failure_count,
                    "last_error": error
                },
                level="WARNING"
            )

    def _record_success(self):
        self._failure_count = 0
        self._circuit_open = False
        self._metrics["success_count"] += 1
        self._metrics["circuit_breaker_status"] = "closed"
        self._metrics["last_attempt_time"] = time.time()

    def invoke(self, prompt: str) -> Optional[str]:
        if not self._metrics["first_attempt_time"]:
            self._metrics["first_attempt_time"] = time.time()

        if self._is_circuit_open():
            logger.structured_log(
                "provider_invoke", "circuit_breaker_open",
                {
                    "context_id": self.context_id,
                    "circuit_breaker_status": "open"
                },
                level="WARNING"
            )
            return None

        for attempt in range(self.max_retries):
            self._metrics["attempt_count"] += 1
            try:
                from gigachat import GigaChat as GigaChatSDK
                from gigachat.models import Chat, Messages, MessagesRole

                logger.structured_log(
                    "provider_invoke", "attempt_start",
                    {
                        "context_id": self.context_id,
                        "attempt_number": attempt + 1,
                        "max_retries": self.max_retries
                    },
                    level="DEBUG-1"
                )

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

                logger.debug(f"[GigaChat] Prompt ({len(prompt)} chars): {prompt[:300]}...")

                self.token_counter.add_prompt(prompt)
                response = client.chat(Chat(messages=messages))
                response_text = response.choices[0].message.content

                logger.debug(f"[GigaChat] Response ({len(response_text)} chars): {response_text[:300]}...")

                self.token_counter.add_completion(response_text)
                self._record_success()

                logger.structured_log(
                    "provider_invoke", "success",
                    {
                        "context_id": self.context_id,
                        "attempt_number": attempt + 1,
                        "prompt_len": len(prompt),
                        "response_len": len(response_text)
                    },
                    level="INFO"
                )

                return response_text

            except ImportError as e:
                error_msg = "gigachat SDK not installed"
                logger.structured_log(
                    "provider_invoke", "import_error",
                    {
                        "context_id": self.context_id,
                        "error": error_msg
                    },
                    level="WARNING"
                )
                self._record_failure(error_msg)
                return None
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                logger.structured_log(
                    "provider_invoke", "attempt_failed",
                    {
                        "context_id": self.context_id,
                        "attempt_number": attempt + 1,
                        "error_type": error_type,
                        "error": error_msg,
                        "will_retry": attempt < self.max_retries - 1
                    },
                    level="WARNING"
                )
                if attempt < self.max_retries - 1:
                    backoff_time = 2 ** attempt
                    time.sleep(backoff_time)
                else:
                    self._record_failure(error_msg)

        return None

    def get_token_usage(self):
        return self.token_counter.get_usage()

    def get_metrics(self) -> dict:
        """Return client metrics for logging and monitoring."""
        return self._metrics.copy()
