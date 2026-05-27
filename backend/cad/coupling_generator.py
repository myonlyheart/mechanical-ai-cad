"""Shaft coupling generator."""

from dataclasses import dataclass
from math import cos, sin, pi
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle, extrude,
    Location, Pos,
    Mode, fillet,
)
from .base_part import BasePart, PartParams
from ..core.models import Anchor
from ..engineering.assembly.anchors import coupling_anchors


@dataclass
class CouplingParams(PartParams):
    outer_diameter: float = 30
    length: float = 40
    bore_diameter: float = 8
    slit_width: float = 1.5
    slit_count: int = 4
    set_screw_diameter: float = 3


class Coupling(BasePart):
    def __init__(self, params: CouplingParams):
        super().__init__(params)
        self.params = params

    def get_anchors(self) -> list[Anchor]:
        return coupling_anchors(
            outer_diameter=self.params.outer_diameter,
            length=self.params.length,
            bore_diameter=self.params.bore_diameter,
        )

    def build(self):
        p = self.params
        outer_r = p.outer_diameter / 2
        half_len = p.length / 2

        with BuildPart() as part:
            # Main body cylinder
            with BuildSketch():
                Circle(outer_r)
            extrude(amount=p.length)

            # Center bore (through)
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch():
                    Circle(p.bore_diameter / 2)
                extrude(amount=p.length * 2, both=True)

            # Slits (flexible element) - radial cuts
            slit_depth = outer_r - p.bore_diameter / 2 - 2
            for i in range(p.slit_count):
                angle = pi * i / p.slit_count
                # Alternate: slits from opposite ends
                if i % 2 == 0:
                    z_start = half_len - p.length * 0.3
                else:
                    z_start = half_len
                x_dir = cos(angle)
                y_dir = sin(angle)
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Location((x_dir * outer_r * 0.5, y_dir * outer_r * 0.5, z_start))):
                        Rectangle(p.slit_width, slit_depth)
                    extrude(amount=p.length * 0.3)

            # Set screw holes (top)
            for i in range(2):
                angle = pi * i
                x = cos(angle) * outer_r
                y = sin(angle) * outer_r
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Location((x, y, half_len))):
                        Circle(p.set_screw_diameter / 2)
                    extrude(amount=outer_r * 2)

        return part.part
