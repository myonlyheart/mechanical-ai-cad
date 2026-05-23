"""Bracket generators for L-brackets and T-brackets."""

from dataclasses import dataclass
from build123d import (
    BuildPart, BuildSketch, BuildLine, Rectangle, Circle,
    extrude, Axis, Location, Vector, Rotation, Pos,
    Mode, Kind, fillet, chamfer,
)
from .base_part import BasePart, PartParams


@dataclass
class LBracketParams(PartParams):
    """Parameters for L-bracket."""
    length: float = 80
    width: float = 40
    height: float = 60
    thickness: float = 5
    hole_diameter: float = 6.5
    hole_count: int = 4
    fillet_radius: float = 2.0


@dataclass
class TBracketParams(PartParams):
    """Parameters for T-bracket."""
    length: float = 100
    width: float = 50
    height: float = 60
    thickness: float = 5
    hole_diameter: float = 6.5
    hole_count: int = 6
    fillet_radius: float = 2.0


class LBracket(BasePart):
    """L-shaped mounting bracket generator."""

    def __init__(self, params: LBracketParams):
        super().__init__(params)
        self.params = params

    def build(self):
        p = self.params
        with BuildPart() as part:
            # Vertical plate
            with BuildSketch() as sketch:
                Rectangle(p.width, p.height)
            extrude(amount=p.thickness)

            # Horizontal plate
            with BuildSketch(Location((0, 0, p.thickness))) as sketch2:
                Rectangle(p.length, p.width)
            extrude(amount=-p.thickness)

            # Mounting holes on vertical plate
            with BuildPart(part.part, mode=Mode.SUBTRACT) as holes:
                if p.hole_count >= 1:
                    with BuildSketch(Location((0, p.height / 4, 0))) as h1:
                        Circle(p.hole_diameter / 2)
                    extrude(amount=p.thickness, mode=Mode.SUBTRACT)
                if p.hole_count >= 2:
                    with BuildSketch(Location((0, -p.height / 4, 0))) as h2:
                        Circle(p.hole_diameter / 2)
                    extrude(amount=p.thickness, mode=Mode.SUBTRACT)

            # Mounting holes on horizontal plate
            with BuildPart(part.part, mode=Mode.SUBTRACT) as holes2:
                if p.hole_count >= 3:
                    with BuildSketch(Location((p.length / 4, 0, p.thickness))) as h3:
                        Circle(p.hole_diameter / 2)
                    extrude(amount=-p.thickness, mode=Mode.SUBTRACT)
                if p.hole_count >= 4:
                    with BuildSketch(Location((-p.length / 4, 0, p.thickness))) as h4:
                        Circle(p.hole_diameter / 2)
                    extrude(amount=-p.thickness, mode=Mode.SUBTRACT)

            # Fillet edges (optional, best-effort)
            try:
                fillet(part.part.edges(), p.fillet_radius)
            except Exception:
                pass

        return part.part


class TBracket(BasePart):
    """T-shaped mounting bracket generator."""

    def __init__(self, params: TBracketParams):
        super().__init__(params)
        self.params = params

    def build(self):
        p = self.params
        with BuildPart() as part:
            # Vertical plate
            with BuildSketch() as sketch:
                Rectangle(p.width, p.height)
            extrude(amount=p.thickness)

            # Horizontal plate (centered)
            with BuildSketch(Location((0, 0, p.thickness))) as sketch2:
                Rectangle(p.length, p.width)
            extrude(amount=-p.thickness)

            # Mounting holes
            with BuildPart(part.part, mode=Mode.SUBTRACT) as holes:
                if p.hole_count >= 1:
                    with BuildSketch(Location((p.length / 4, 0, p.thickness))) as h1:
                        Circle(p.hole_diameter / 2)
                    extrude(amount=-p.thickness, mode=Mode.SUBTRACT)
                if p.hole_count >= 2:
                    with BuildSketch(Location((-p.length / 4, 0, p.thickness))) as h2:
                        Circle(p.hole_diameter / 2)
                    extrude(amount=-p.thickness, mode=Mode.SUBTRACT)

            try:
                fillet(part.part.edges(), p.fillet_radius)
            except Exception:
                pass

        return part.part
