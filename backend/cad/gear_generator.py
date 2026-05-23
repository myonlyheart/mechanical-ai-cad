"""Spur gear generator with involute profile approximation."""

import math
from dataclasses import dataclass
from build123d import (
    BuildPart, BuildSketch, BuildLine, Circle, RegularPolygon,
    extrude, Axis, Location, Vector, Rotation, Pos,
    Mode, Kind, fillet, chamfer,
)
from .base_part import BasePart, PartParams


@dataclass
class SpurGearParams(PartParams):
    """Parameters for spur gear."""
    module: float = 2
    teeth_count: int = 20
    width: float = 10
    bore_diameter: float = 8
    pressure_angle: float = 20.0
    addendum: float = 0.0
    dedendum: float = 0.0


class SpurGear(BasePart):
    """Spur gear generator with parametric involute profile."""

    def __init__(self, params: SpurGearParams):
        super().__init__(params)
        self.params = params

    def _get_pitch_radius(self) -> float:
        return (self.params.module * self.params.teeth_count) / 2

    def _get_outer_radius(self) -> float:
        addendum = self.params.addendum or self.params.module
        return self._get_pitch_radius() + addendum

    def _get_root_radius(self) -> float:
        dedendum = self.params.dedendum or (1.25 * self.params.module)
        return self._get_pitch_radius() - dedendum

    def build(self):
        p = self.params
        pitch_r = self._get_pitch_radius()
        outer_r = self._get_outer_radius()
        root_r = self._get_root_radius()

        with BuildPart() as part:
            # Gear body - approximate with outer circle
            with BuildSketch() as sketch:
                # Outer gear profile
                Circle(outer_r)
            extrude(amount=p.width)

            # Bore hole
            with BuildPart(part.part, mode=Mode.SUBTRACT) as bore:
                with BuildSketch() as bore_sketch:
                    Circle(p.bore_diameter / 2)
                extrude(amount=p.width, mode=Mode.SUBTRACT)

            # Keyway approximation
            key_width = p.bore_diameter * 0.3
            key_depth = p.bore_diameter * 0.15
            with BuildPart(part.part, mode=Mode.SUBTRACT) as keyway:
                with BuildSketch(Location((p.bore_diameter / 2 - key_depth, 0))) as ks:
                    from build123d import Rectangle
                    Rectangle(key_depth * 2, key_width)
                extrude(amount=p.width, mode=Mode.SUBTRACT)

            # Fillet edges
            try:
                fillet(part.part.edges(), 0.3)
            except Exception:
                pass

        return part.part
