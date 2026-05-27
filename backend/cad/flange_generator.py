"""Circular flange generator."""

from dataclasses import dataclass
from math import cos, sin, pi
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle, extrude,
    Location, Pos,
    Mode, fillet,
)
from .base_part import BasePart, PartParams
from ..core.models import Anchor
from ..engineering.assembly.anchors import flange_anchors


@dataclass
class FlangeParams(PartParams):
    outer_diameter: float = 80
    inner_diameter: float = 50
    thickness: float = 8
    bolt_hole_diameter: float = 8
    bolt_count: int = 6
    bolt_circle_diameter: float = 68
    bore_diameter: float = 30


class Flange(BasePart):
    def __init__(self, params: FlangeParams):
        super().__init__(params)
        self.params = params

    def get_anchors(self) -> list[Anchor]:
        return flange_anchors(
            outer_diameter=self.params.outer_diameter,
            bore_diameter=self.params.bore_diameter,
            thickness=self.params.thickness,
            bolt_circle_diameter=self.params.bolt_circle_diameter,
            bolt_count=self.params.bolt_count,
            bolt_hole_diameter=self.params.bolt_hole_diameter,
        )

    def build(self):
        p = self.params
        outer_r = p.outer_diameter / 2
        bolt_r = p.bolt_circle_diameter / 2

        with BuildPart() as part:
            # Flange body (outer circle)
            with BuildSketch():
                Circle(outer_r)
            extrude(amount=p.thickness)

            # Center bore
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch():
                    Circle(p.bore_diameter / 2)
                extrude(amount=p.thickness * 2, both=True)

            # Bolt holes in circular pattern
            for i in range(p.bolt_count):
                angle = 2 * pi * i / p.bolt_count
                x = bolt_r * cos(angle)
                y = bolt_r * sin(angle)
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(x, y, 0)):
                        Circle(p.bolt_hole_diameter / 2)
                    extrude(amount=p.thickness * 2, both=True)

        return part.part
