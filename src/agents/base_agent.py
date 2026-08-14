from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSubagent(ABC):
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        pass
