from abc import ABC, abstractmethod

class BaseClient(ABC):
    @abstractmethod
    async def chat(self, prompt, max_tokens=None):
        pass
