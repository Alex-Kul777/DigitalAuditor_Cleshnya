from abc import ABC, abstractmethod
from core.llm import get_llm
from core.logger import setup_logger

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.llm = get_llm()
        self.logger = setup_logger(f"agent.{name}")
    
    @abstractmethod
    def execute(self, task: str) -> str:
        pass
