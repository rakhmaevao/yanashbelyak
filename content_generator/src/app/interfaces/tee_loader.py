from abc import ABC, abstractmethod
from src.gramps_tree import GrampsTree


class ITreeLoader(ABC):
    @abstractmethod
    def load(self) -> GrampsTree:
        pass
