import os
import requests
import uuid
from core.logger import setup_logger
from core.config import GIGACHAT_TIMEOUT, GIGACHAT_MAX_RETRIES

logger = setup_logger("llm")


class GigaChatWrapper:
    def __init__(self, api_key: str, model: str, temperature: float = 0.3, timeout: int = 60, max_retries: int = 3, scope: str = "GIGACHAT_API_B2B", context_id: str = None):
        from core.gigachat_client import GigaChatClient
        self.client = GigaChatClient(api_key=api_key, model=model, max_retries=max_retries, timeout=timeout, scope=scope, context_id=context_id)
        self.temperature = temperature
        self.context_id = context_id

    def invoke(self, prompt: str) -> str:
        response = self.client.invoke(prompt)
        if response is None:
            raise RuntimeError("GigaChat failed and no fallback available")
        return response

    def get_metrics(self) -> dict:
        return self.client.get_metrics()


class LLMFactory:
    _gigachat_available = None
    _context_id = None

    @classmethod
    def _check_gigachat(cls, context_id: str = None, reason: str = "hybrid_selection") -> bool:
        if cls._gigachat_available is None:
            from core.gigachat_validator import GigaChatValidator
            validator = GigaChatValidator(context_id=context_id)
            cls._gigachat_available = validator.is_available(reason=reason, context_id=context_id)
            if cls._gigachat_available:
                logger.structured_log(
                    "provider_selection", "gigachat_available",
                    {"context_id": context_id, "reason": reason},
                    level="INFO"
                )
            else:
                logger.structured_log(
                    "provider_selection", "gigachat_unavailable",
                    {"context_id": context_id, "reason": reason},
                    level="INFO"
                )
        return cls._gigachat_available

    @classmethod
    def get_llm(cls, temperature: float = None, mode: str = "default", context_id: str = None):
        """Get LLM instance with optional mode selection for two-pass review (S1/S2).

        Args:
            temperature: Override default temp for mode. If None, uses mode default.
            mode: "default" (0.3), "cheap" (0.1, S1 fast), "deep" (0.2, S2 strong)
            context_id: Optional tracing ID for logging provider selection chain

        Returns:
            BaseLLM instance (OllamaLLM, GigaChatLLMAdapter, etc.)
        """
        if context_id is None:
            context_id = str(uuid.uuid4())[:8]
        cls._context_id = context_id

        # Mode defaults + env var mapping
        mode_config = {
            "cheap": {"temp": 0.1, "provider_env": "LLM_S1_PROVIDER", "model_env": "LLM_S1_MODEL"},
            "deep": {"temp": 0.2, "provider_env": "LLM_S2_PROVIDER", "model_env": "LLM_S2_MODEL"},
            "default": {"temp": 0.3, "provider_env": "LLM_PROVIDER", "model_env": None}
        }

        if mode not in mode_config:
            logger.structured_log(
                "provider_selection", "unknown_mode",
                {"context_id": context_id, "mode": mode},
                level="WARNING"
            )
            mode = "default"

        config = mode_config[mode]
        if temperature is None:
            temperature = config["temp"]

        # Get provider from mode-specific env or fallback to default
        provider = os.getenv(config["provider_env"], os.getenv("LLM_PROVIDER", "hybrid")).lower()

        fallback_reason = None
        if provider == "hybrid":
            logger.structured_log(
                "provider_selection", "hybrid_mode_checking",
                {"context_id": context_id, "mode": mode},
                level="DEBUG-1"
            )
            if cls._check_gigachat(context_id=context_id, reason="hybrid_selection"):
                provider = "gigachat"
            else:
                provider = "ollama"
                fallback_reason = "gigachat_unavailable"

        logger.structured_log(
            "provider_selection", "selected",
            {
                "context_id": context_id,
                "mode": mode,
                "provider": provider,
                "temperature": temperature,
                "fallback_reason": fallback_reason
            },
            level="INFO"
        )

        return cls._build(provider, None, temperature, context_id=context_id)

    @classmethod
    def _build(cls, provider: str, model: str = None, temperature: float = 0.3, context_id: str = None):
        """Build LLM instance for given provider.

        Args:
            provider: "gigachat", "ollama", "anthropic", "openai"
            model: Optional model override (uses env var if None)
            temperature: Model temperature
            context_id: Optional tracing ID

        Returns:
            BaseLLM instance
        """
        if provider == "gigachat":
            return cls._get_gigachat(temperature, context_id=context_id)
        elif provider == "anthropic":
            return cls._get_anthropic(temperature)
        elif provider == "openai":
            return cls._get_openai(temperature)
        else:
            return cls._get_ollama(temperature)

    @classmethod
    def _get_gigachat(cls, temperature: float, context_id: str = None):
        api_key = os.getenv("GIGACHAT_API_KEY")
        if not api_key:
            raise ValueError(
                "GigaChat provider requested but GIGACHAT_API_KEY is not set. "
                "Set it in .env or export GIGACHAT_API_KEY=<your_api_key>"
            )
        wrapper = GigaChatWrapper(
            api_key=api_key,
            model=os.getenv("GIGACHAT_MODEL", "GigaChat-2-Max"),
            temperature=temperature,
            timeout=GIGACHAT_TIMEOUT,
            max_retries=GIGACHAT_MAX_RETRIES,
            scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_B2B"),
            context_id=context_id
        )

        def invoke_with_fallback(prompt: str) -> str:
            try:
                return wrapper.invoke(prompt)
            except Exception as e:
                logger.structured_log(
                    "provider_fallback", "gigachat_error",
                    {
                        "context_id": context_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "fallback_to": "ollama"
                    },
                    level="WARNING"
                )
                ollama_llm = cls._get_ollama(temperature)
                return ollama_llm.invoke(prompt)

        from langchain_core.language_models.llms import BaseLLM
        from langchain_core.callbacks import CallbackManagerForLLMRun
        from typing import Optional, List, Any
        from langchain_core.outputs import LLMResult, Generation
        from pydantic import Field

        class GigaChatLLMAdapter(BaseLLM):
            temperature: float = Field(default=0.3)

            def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> Any:
                generations = []
                for prompt in prompts:
                    text = invoke_with_fallback(prompt)
                    generations.append([Generation(text=text)])
                return LLMResult(generations=generations)

            def _llm_type(self) -> str:
                return "gigachat-adapter"

        return GigaChatLLMAdapter(temperature=temperature)

    @classmethod
    def _get_ollama(cls, temperature: float):
        from langchain_ollama import OllamaLLM

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            response = requests.get(f"{base_url}/api/tags", timeout=2)
            if response.status_code != 200:
                logger.warning(f"Ollama server not responding correctly: {response.status_code}")
        except Exception as e:
            logger.error(f"Ollama server is not running at {base_url}. Start it with: ollama serve")
            raise ConnectionError(f"Ollama unavailable: {e}")

        return OllamaLLM(
            base_url=base_url,
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


def get_llm(temperature: float = None, mode: str = "default"):
    """Convenience function. See LLMFactory.get_llm() for docs."""
    return LLMFactory.get_llm(temperature=temperature, mode=mode)
