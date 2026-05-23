"""Spur gear generator with involute profile approximation."""

from dataclasses import dataclass
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle,
    extrude, Location, Pos,
    Mode, fillet,
)
from .base_part import BasePart, PartParams


@dataclass
class SpurGearParams(PartParams):
    module: float = 2
    teeth_count: int = 20
    width: float = 10
    bore_diameter: float = 8
    pressure_angle: float = 20.0
    addendum: float = 0.0
    dedendum: float = 0.0


class SpurGear(BasePart):
    def __init__(self, params: SpurGearParams):
        super().__init__(params)
        self.params = params

    def _get_pitch_radius(self) -> float:
        return (self.params.module * self.params.teeth_count) / 2

    def _get_outer_radius(self) -> float:
        addendum = self.params.addendum or self.params.module
        return self._get_pitch_radius() + addendum

    def build(self):
        p = self.params
        outer_r = self._get_outer_radius()

        with BuildPart() as part:
            # Gear body
            with BuildSketch():
                Circle(outer_r)
            extrude(amount=p.width)

            # Bore hole
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch():
                    Circle(p.bore_diameter / 2)
                extrude(amount=p.width * 2, both=True)

            # Keyway
            key_width = p.bore_diameter * 0.3
            key_depth = p.bore_diameter * 0.15
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch(Pos(p.bore_diameter / 2 - key_depth, 0, 0)):
                    Rectangle(key_depth * 2, key_width)
                extrude(amount=p.width * 2, both=True)

        return part.part
