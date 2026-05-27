"""Base classes for parametric CAD parts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from abc import ABC, abstractmethod

from ..core.models import Part, Anchor


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

    def get_anchors(self) -> list[Anchor]:
        """Return default anchors for this part. Override in subclasses."""
        return []

    def build_part(self) -> Part:
        """Build geometry and return unified Part object."""
        geometry = self.build()
        return Part(
            name=self.params.name,
            part_type=self.__class__.__name__.lower().replace("mount", "_mount"),
            parameters=self._params_to_dict(),
            geometry=geometry,
            anchors=self.get_anchors(),
            metadata={"material": self.params.material},
        )

    def _params_to_dict(self) -> dict[str, Any]:
        """Convert params to dictionary."""
        if hasattr(self.params, "__dict__"):
            return dict(self.params.__dict__)
        return {}

    def get_info(self) -> dict:
        """Return part information as a dictionary."""
        return {
            "name": self.params.name,
            "material": self.params.material,
            "type": self.__class__.__name__,
        }
