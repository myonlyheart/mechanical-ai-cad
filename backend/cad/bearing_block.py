"""Pillow block bearing housing generator."""

from dataclasses import dataclass
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle, extrude,
    Location, Pos,
    Mode, fillet,
)
from .base_part import BasePart, PartParams
from ..core.models import Anchor
from ..engineering.assembly.anchors import bearing_block_anchors


@dataclass
class BearingBlockParams(PartParams):
    base_length: float = 60
    base_width: float = 40
    base_thickness: float = 8
    bearing_diameter: float = 22
    bearing_depth: float = 7
    mounting_hole_diameter: float = 5
    mounting_hole_spacing: float = 45
    height: float = 30
    fillet_radius: float = 2.0


class BearingBlock(BasePart):
    def __init__(self, params: BearingBlockParams):
        super().__init__(params)
        self.params = params

    def get_anchors(self) -> list[Anchor]:
        return bearing_block_anchors(
            base_length=self.params.base_length,
            base_width=self.params.base_width,
            height=self.params.height,
            bearing_diameter=self.params.bearing_diameter,
            mounting_hole_spacing=self.params.mounting_hole_spacing,
        )

    def build(self):
        p = self.params
        body_height = p.height - p.base_thickness
        bearing_r = p.bearing_diameter / 2

        with BuildPart() as part:
            # Base plate
            with BuildSketch():
                Rectangle(p.base_length, p.base_width)
            extrude(amount=p.base_thickness)

            # Bearing housing body (pillars)
            with BuildSketch(Pos(0, 0, p.base_thickness)):
                Rectangle(p.bearing_diameter + p.base_thickness * 2, p.base_width)
            extrude(amount=body_height)

            # Bearing bore (through the housing)
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch(Pos(0, 0, p.base_thickness + body_height / 2)):
                    Circle(bearing_r)
                extrude(amount=p.base_width * 2, both=True)

            # Mounting holes on base
            for x_off in [-p.mounting_hole_spacing / 2, p.mounting_hole_spacing / 2]:
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(x_off, 0, 0)):
                        Circle(p.mounting_hole_diameter / 2)
                    extrude(amount=p.base_thickness * 2, both=True)

        return part.part
