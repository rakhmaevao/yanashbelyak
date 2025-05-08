from abc import ABC, abstractmethod
from src.app.entities import GrampsTree


class ITreeLoader(ABC):
    @abstractmethod
    def load(self) -> GrampsTree:
        pass
