from langchain_ollama import OllamaLLM
from core.config import OLLAMA_BASE_URL, OLLAMA_MODEL

def get_llm(temperature: float = 0.3):
    return OllamaLLM(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=temperature,
        num_ctx=8192,
    )
