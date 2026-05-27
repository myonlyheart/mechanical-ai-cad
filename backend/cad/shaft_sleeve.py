"""Shaft sleeve / bushing generator."""

from dataclasses import dataclass
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle, extrude,
    Location, Pos,
    Mode, fillet,
)
from .base_part import BasePart, PartParams
from ..core.models import Anchor
from ..engineering.assembly.anchors import shaft_sleeve_anchors


@dataclass
class ShaftSleeveParams(PartParams):
    outer_diameter: float = 20
    inner_diameter: float = 12
    length: float = 30
    flange_diameter: float = 28
    flange_thickness: float = 3
    keyway_width: float = 4
    keyway_depth: float = 2


class ShaftSleeve(BasePart):
    def __init__(self, params: ShaftSleeveParams):
        super().__init__(params)
        self.params = params

    def get_anchors(self) -> list[Anchor]:
        return shaft_sleeve_anchors(
            outer_diameter=self.params.outer_diameter,
            inner_diameter=self.params.inner_diameter,
            length=self.params.length,
            flange_diameter=self.params.flange_diameter,
            flange_thickness=self.params.flange_thickness,
        )

    def build(self):
        p = self.params
        outer_r = p.outer_diameter / 2
        inner_r = p.inner_diameter / 2

        with BuildPart() as part:
            # Main sleeve body
            with BuildSketch():
                Circle(outer_r)
            extrude(amount=p.length)

            # Center bore
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch():
                    Circle(inner_r)
                extrude(amount=p.length * 2, both=True)

            # Flange at one end
            flange_r = p.flange_diameter / 2
            with BuildSketch(Location((0, 0, 0))):
                Circle(flange_r)
            extrude(amount=p.flange_thickness)

            # Center bore through flange
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch():
                    Circle(inner_r)
                extrude(amount=p.flange_thickness * 2, both=True)

            # Keyway on inner bore
            kw_w = p.keyway_width
            kw_d = p.keyway_depth
            kw_y = inner_r + kw_d / 2
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch(Pos(0, kw_y, 0)):
                    Rectangle(kw_w, kw_d)
                extrude(amount=p.length * 2, both=True)

        return part.part
