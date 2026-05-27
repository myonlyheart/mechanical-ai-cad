"""Bracket generators for L-brackets and T-brackets."""

from dataclasses import dataclass
from build123d import (
    BuildPart, BuildSketch, Rectangle, Circle,
    extrude, Location, Pos,
    Mode, fillet,
)
from .base_part import BasePart, PartParams
from ..core.models import Anchor
from ..engineering.assembly.anchors import l_bracket_anchors, t_bracket_anchors


@dataclass
class LBracketParams(PartParams):
    length: float = 80
    width: float = 40
    height: float = 60
    thickness: float = 5
    hole_diameter: float = 6.5
    hole_count: int = 4
    fillet_radius: float = 2.0


@dataclass
class TBracketParams(PartParams):
    length: float = 100
    width: float = 50
    height: float = 60
    thickness: float = 5
    hole_diameter: float = 6.5
    hole_count: int = 6
    fillet_radius: float = 2.0


def _add_cylindrical_cut(parent, center, diameter, depth):
    """Add a cylindrical cut using BuildPart on the parent object."""
    with BuildPart(parent, mode=Mode.SUBTRACT) as cut:
        with BuildSketch(Location(center)) as s:
            Circle(diameter / 2)
        extrude(amount=depth, both=True)


class LBracket(BasePart):
    def __init__(self, params: LBracketParams):
        super().__init__(params)
        self.params = params

    def get_anchors(self) -> list[Anchor]:
        return l_bracket_anchors(
            length=self.params.length,
            width=self.params.width,
            height=self.params.height,
            thickness=self.params.thickness,
            hole_diameter=self.params.hole_diameter,
        )

    def build(self):
        p = self.params

        with BuildPart() as part:
            # Vertical plate
            with BuildSketch(Pos(0, 0, 0)) as s1:
                Rectangle(p.width, p.height)
            extrude(amount=p.thickness)

            # Horizontal plate attached at bottom of vertical
            with BuildSketch(Pos(0, 0, 0)) as s2:
                Rectangle(p.length, p.width)
            extrude(amount=-p.thickness)

            # Holes on vertical plate
            if p.hole_count >= 1:
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(0, p.height / 4, p.thickness / 2)):
                        Circle(p.hole_diameter / 2)
                    extrude(amount=p.thickness * 2, both=True)

            if p.hole_count >= 2:
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(0, -p.height / 4, p.thickness / 2)):
                        Circle(p.hole_diameter / 2)
                    extrude(amount=p.thickness * 2, both=True)

            # Holes on horizontal plate
            if p.hole_count >= 3:
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(p.length / 4, 0, -p.thickness / 2)):
                        Circle(p.hole_diameter / 2)
                    extrude(amount=p.thickness * 2, both=True)

            if p.hole_count >= 4:
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(-p.length / 4, 0, -p.thickness / 2)):
                        Circle(p.hole_diameter / 2)
                    extrude(amount=p.thickness * 2, both=True)

        return part.part


class TBracket(BasePart):
    def __init__(self, params: TBracketParams):
        super().__init__(params)
        self.params = params

    def get_anchors(self) -> list[Anchor]:
        return t_bracket_anchors(
            length=self.params.length,
            width=self.params.width,
            height=self.params.height,
            thickness=self.params.thickness,
            hole_diameter=self.params.hole_diameter,
        )

    def build(self):
        p = self.params

        with BuildPart() as part:
            # Vertical plate
            with BuildSketch() as s1:
                Rectangle(p.width, p.height)
            extrude(amount=p.thickness)

            # Horizontal plate centered
            with BuildSketch(Pos(0, 0, 0)) as s2:
                Rectangle(p.length, p.width)
            extrude(amount=-p.thickness)

            # Holes on horizontal plate
            if p.hole_count >= 1:
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(p.length / 4, 0, -p.thickness / 2)):
                        Circle(p.hole_diameter / 2)
                    extrude(amount=p.thickness * 2, both=True)

            if p.hole_count >= 2:
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(-p.length / 4, 0, -p.thickness / 2)):
                        Circle(p.hole_diameter / 2)
                    extrude(amount=p.thickness * 2, both=True)

        return part.part
