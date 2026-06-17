import os
import requests
from typing import Optional
from core.logger import setup_logger

logger = setup_logger("gigachat_validator")


class GigaChatValidator:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30, context_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("GIGACHAT_API_KEY")
        self.timeout = timeout
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.context_id = context_id

    def validate_api_key(self) -> bool:
        if not self.api_key:
            logger.structured_log(
                "provider_check", "gigachat_api_key_missing",
                {"context_id": self.context_id, "reason": "config_validation"},
                level="WARNING"
            )
            return False
        return True

    def check_connection(self, reason: str = "availability_check") -> bool:
        if not self.validate_api_key():
            return False

        import time
        start_time = time.time()
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
            latency_ms = int((time.time() - start_time) * 1000)
            if response.status_code == 200:
                logger.structured_log(
                    "provider_check", "gigachat_connection_success",
                    {
                        "context_id": self.context_id,
                        "reason": reason,
                        "status_code": response.status_code,
                        "latency_ms": latency_ms
                    },
                    level="INFO"
                )
                return True
            else:
                logger.structured_log(
                    "provider_check", "gigachat_connection_failed",
                    {
                        "context_id": self.context_id,
                        "reason": reason,
                        "status_code": response.status_code,
                        "latency_ms": latency_ms
                    },
                    level="WARNING"
                )
                return False
        except requests.exceptions.Timeout:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.structured_log(
                "provider_check", "gigachat_timeout",
                {
                    "context_id": self.context_id,
                    "reason": reason,
                    "timeout_ms": self.timeout * 1000,
                    "actual_latency_ms": latency_ms
                },
                level="WARNING"
            )
            return False
        except requests.exceptions.ConnectionError:
            logger.structured_log(
                "provider_check", "gigachat_connection_error",
                {
                    "context_id": self.context_id,
                    "reason": reason,
                    "error_type": "connection_error"
                },
                level="WARNING"
            )
            return False
        except Exception as e:
            logger.structured_log(
                "provider_check", "gigachat_check_failed",
                {
                    "context_id": self.context_id,
                    "reason": reason,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                level="DEBUG-1"
            )
            return False

    def is_available(self, reason: str = "availability_check", context_id: Optional[str] = None) -> bool:
        if context_id:
            self.context_id = context_id
        return self.check_connection(reason=reason)
