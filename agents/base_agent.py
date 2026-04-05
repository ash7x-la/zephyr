from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, client):
        self.client = client
