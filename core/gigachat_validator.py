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
