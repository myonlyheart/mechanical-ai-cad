"""Base classes for parametric CAD parts."""

from __future__ import annotations

import uuid
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


@dataclass
class MechanicalPart:
    """统一机械零件标准（方案书要求）。

    每个零件必须包含：
    - 工程语义 (category, part_type)
    - 装配语义 (anchors, constraints)
    - 制造语义 (manufacturing_method)
    - 材料语义 (material)
    """
    id: str = ""
    name: str = ""
    category: str = ""                  # fasteners, shafts, gears, bearings, ...
    part_type: str = ""                 # bolt, nut, washer, gear, shaft, ...
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    geometry: Any = None
    anchors: list[Anchor] = field(default_factory=list)
    constraints: list[dict] = field(default_factory=list)
    material: str = "steel"
    manufacturing_method: str = "CNC"

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "part_type": self.part_type,
            "parameters": self.parameters,
            "material": self.material,
            "manufacturing_method": self.manufacturing_method,
            "anchors": [a.name if hasattr(a, "name") else str(a) for a in self.anchors],
            "constraints": self.constraints,
            "metadata": self.metadata,
        }


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

    def to_mechanical_part(self, category: str = "", part_type: str = "") -> MechanicalPart:
        """Convert to MechanicalPart (工程语义层)."""
        geometry = self.build()
        return MechanicalPart(
            name=self.params.name,
            category=category or self.__class__.__name__.lower(),
            part_type=part_type or self.__class__.__name__.lower(),
            parameters=self._params_to_dict(),
            geometry=geometry,
            anchors=self.get_anchors(),
            material=self.params.material,
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
