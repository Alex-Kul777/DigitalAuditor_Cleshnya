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
