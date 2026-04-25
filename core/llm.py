import os
import requests
from core.logger import setup_logger

logger = setup_logger("llm")


class GigaChatWrapper:
    def __init__(self, api_key: str, model: str, temperature: float = 0.3, timeout: int = 60, max_retries: int = 3, scope: str = "GIGACHAT_API_B2B"):
        from core.gigachat_client import GigaChatClient
        self.client = GigaChatClient(api_key=api_key, model=model, max_retries=max_retries, timeout=timeout, scope=scope)
        self.temperature = temperature

    def invoke(self, prompt: str) -> str:
        response = self.client.invoke(prompt)
        if response is None:
            raise RuntimeError("GigaChat failed and no fallback available")
        return response


class LLMFactory:
    _gigachat_available = None

    @classmethod
    def _check_gigachat(cls) -> bool:
        if cls._gigachat_available is None:
            from core.gigachat_validator import GigaChatValidator
            validator = GigaChatValidator()
            cls._gigachat_available = validator.is_available()
            if cls._gigachat_available:
                logger.info("GigaChat is available")
            else:
                logger.info("GigaChat is not available")
        return cls._gigachat_available

    @classmethod
    def get_llm(cls, temperature: float = None, mode: str = "default"):
        """Get LLM instance with optional mode selection for two-pass review (S1/S2).

        Args:
            temperature: Override default temp for mode. If None, uses mode default.
            mode: "default" (0.3), "cheap" (0.1, S1 fast), "deep" (0.2, S2 strong)

        Returns:
            BaseLLM instance (OllamaLLM, GigaChatLLMAdapter, etc.)
        """
        # Mode defaults + env var mapping
        mode_config = {
            "cheap": {"temp": 0.1, "provider_env": "LLM_S1_PROVIDER", "model_env": "LLM_S1_MODEL"},
            "deep": {"temp": 0.2, "provider_env": "LLM_S2_PROVIDER", "model_env": "LLM_S2_MODEL"},
            "default": {"temp": 0.3, "provider_env": "LLM_PROVIDER", "model_env": None}
        }

        if mode not in mode_config:
            logger.warning(f"Unknown mode '{mode}', falling back to 'default'")
            mode = "default"

        config = mode_config[mode]
        if temperature is None:
            temperature = config["temp"]

        # Get provider from mode-specific env or fallback to default
        provider = os.getenv(config["provider_env"], os.getenv("LLM_PROVIDER", "hybrid")).lower()

        if provider == "hybrid":
            if cls._check_gigachat():
                provider = "gigachat"
            else:
                provider = "ollama"

        logger.info(f"Selected LLM: mode={mode}, provider={provider}, temp={temperature}")

        return cls._build(provider, None, temperature)

    @classmethod
    def _build(cls, provider: str, model: str = None, temperature: float = 0.3):
        """Build LLM instance for given provider.

        Args:
            provider: "gigachat", "ollama", "anthropic", "openai"
            model: Optional model override (uses env var if None)
            temperature: Model temperature

        Returns:
            BaseLLM instance
        """
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
            max_retries=int(os.getenv("GIGACHAT_MAX_RETRIES", "3")),
            scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_B2B")
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
