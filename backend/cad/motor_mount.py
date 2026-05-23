"""NEMA17 motor mount generator."""

from dataclasses import dataclass
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle, extrude,
    Location, Pos,
    Mode, fillet,
)
from .base_part import BasePart, PartParams


@dataclass
class NEMA17MountParams(PartParams):
    base_length: float = 60
    base_width: float = 60
    base_thickness: float = 5
    mount_height: float = 40
    motor_hole_spacing: float = 31.0
    center_bore: float = 22.0
    mounting_hole_diameter: float = 4.0
    base_hole_diameter: float = 5.0


class NEMA17Mount(BasePart):
    def __init__(self, params: NEMA17MountParams):
        super().__init__(params)
        self.params = params

    def build(self):
        p = self.params
        half_spacing = p.motor_hole_spacing / 2
        base_depth = p.base_thickness + p.mount_height

        with BuildPart() as part:
            # Base plate
            with BuildSketch():
                Rectangle(p.base_length, p.base_width)
            extrude(amount=p.base_thickness)

            # Vertical mount plate
            with BuildSketch(Pos(0, -p.base_width / 2, 0)):
                Rectangle(p.base_length, p.mount_height)
            extrude(amount=-p.base_thickness)

            # Center bore
            bore_y = -p.base_width / 2 + p.mount_height / 2
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch(Pos(0, bore_y, 0)):
                    Circle(p.center_bore / 2)
                extrude(amount=base_depth * 2, both=True)

            # Motor mounting holes
            for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                x = dx * half_spacing
                y = bore_y + dy * half_spacing
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(x, y, 0)):
                        Circle(p.mounting_hole_diameter / 2)
                    extrude(amount=base_depth * 2, both=True)

            # Base mounting holes
            for x_off in [-p.base_length / 3, p.base_length / 3]:
                for y_off in [-p.base_width / 3, p.base_width / 3]:
                    with BuildPart(mode=Mode.SUBTRACT):
                        with BuildSketch(Pos(x_off, y_off, 0)):
                            Circle(p.base_hole_diameter / 2)
                        extrude(amount=base_depth * 2, both=True)

        return part.part
