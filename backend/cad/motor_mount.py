"""NEMA17 motor mount generator."""

from dataclasses import dataclass
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle, extrude,
    Axis, Location, Vector, Rotation, Pos,
    Mode, Kind, fillet, chamfer,
)
from .base_part import BasePart, PartParams


@dataclass
class NEMA17MountParams(PartParams):
    """Parameters for NEMA17 motor mount."""
    base_length: float = 60
    base_width: float = 60
    base_thickness: float = 5
    mount_height: float = 40
    motor_hole_spacing: float = 31.0
    center_bore: float = 22.0
    mounting_hole_diameter: float = 4.0
    base_hole_diameter: float = 5.0


class NEMA17Mount(BasePart):
    """NEMA17 stepper motor mounting plate."""

    def __init__(self, params: NEMA17MountParams):
        super().__init__(params)
        self.params = params

    def build(self):
        p = self.params
        half_spacing = p.motor_hole_spacing / 2

        with BuildPart() as part:
            # Base plate
            with BuildSketch() as base_sketch:
                Rectangle(p.base_length, p.base_width)
            extrude(amount=p.base_thickness)

            # Vertical mount plate
            with BuildSketch(Location((0, -p.base_width / 2, p.base_thickness))) as vert_sketch:
                Rectangle(p.base_length, p.mount_height)
            extrude(amount=-p.base_thickness)

            # Center bore for motor shaft
            with BuildPart(part.part, mode=Mode.SUBTRACT) as bore:
                with BuildSketch(Location((0, -p.base_width / 2 + p.mount_height / 2, 0))) as cs:
                    Circle(p.center_bore / 2)
                extrude(amount=p.base_thickness, mode=Mode.SUBTRACT)

            # Motor mounting holes (4 corners)
            with BuildPart(part.part, mode=Mode.SUBTRACT) as motor_holes:
                hole_loc = Location((0, -p.base_width / 2 + p.mount_height / 2, 0))
                for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    x = dx * half_spacing
                    y = -p.base_width / 2 + p.mount_height / 2 + dy * half_spacing
                    with BuildSketch(Location((x, y, 0))) as hs:
                        Circle(p.mounting_hole_diameter / 2)
                    extrude(amount=p.base_thickness, mode=Mode.SUBTRACT)

            # Base mounting holes
            with BuildPart(part.part, mode=Mode.SUBTRACT) as base_holes:
                for x_offset in [-p.base_length / 3, p.base_length / 3]:
                    for y_offset in [-p.base_width / 3, p.base_width / 3]:
                        with BuildSketch(Location((x_offset, y_offset, 0))) as hs:
                            Circle(p.base_hole_diameter / 2)
                        extrude(amount=p.base_thickness, mode=Mode.SUBTRACT)

            # Fillet
            try:
                fillet(part.part.edges(), 1.5)
            except Exception:
                pass

        return part.part
