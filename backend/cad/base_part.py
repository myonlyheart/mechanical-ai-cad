"""Base classes for parametric CAD parts."""

from dataclasses import dataclass, field
from typing import Optional
from abc import ABC, abstractmethod


@dataclass
class PartParams:
    """Base parameters for all parts."""
    name: str = "part"
    material: str = "steel"
    tolerance: float = 0.1


class BasePart(ABC):
    """Abstract base class for all CAD parts."""

    def __init__(self, params: PartParams):
        self.params = params

    @abstractmethod
    def build(self):
        """Build and return the part geometry."""
        pass

    def get_info(self) -> dict:
        """Return part information as a dictionary."""
        return {
            "name": self.params.name,
            "material": self.params.material,
            "type": self.__class__.__name__,
        }
