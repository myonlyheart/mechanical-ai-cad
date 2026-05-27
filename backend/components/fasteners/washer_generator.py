"""Washer generator - 平垫、弹簧垫、锁紧垫。"""

from dataclasses import dataclass
from build123d import (
    BuildPart, BuildSketch, Circle,
    extrude, Pos, Mode,
)
from ...cad.base_part import BasePart, PartParams
from ...core.models import Anchor
from ...engineering.assembly.anchors import (
    create_face_anchor, create_axis_anchor,
)

# ISO 标准垫片尺寸 (diameter -> dimensions)
WASHER_DIMS = {
    3: {"inner": 3.2, "outer": 7.0, "thickness": 0.5},
    4: {"inner": 4.3, "outer": 9.0, "thickness": 0.8},
    5: {"inner": 5.3, "outer": 10.0, "thickness": 1.0},
    6: {"inner": 6.4, "outer": 12.0, "thickness": 1.6},
    8: {"inner": 8.4, "outer": 16.0, "thickness": 1.6},
    10: {"inner": 10.5, "outer": 20.0, "thickness": 2.0},
    12: {"inner": 13.0, "outer": 24.0, "thickness": 2.5},
    16: {"inner": 17.0, "outer": 30.0, "thickness": 3.0},
    20: {"inner": 21.0, "outer": 37.0, "thickness": 3.0},
}


@dataclass
class WasherParams(PartParams):
    inner_diameter: float = 6.5
    outer_diameter: float = 12.0
    thickness: float = 1.6
    washer_type: str = "flat"       # flat, spring, lock


class Washer(BasePart):
    def __init__(self, params: WasherParams):
        super().__init__(params)
        self.params = params

    def get_anchors(self) -> list[Anchor]:
        p = self.params
        return [
            create_face_anchor(
                "top_face", position=(0, 0, p.thickness),
                normal=(0, 0, 1), metadata={"description": "垫片顶面"},
            ),
            create_face_anchor(
                "bottom_face", position=(0, 0, 0),
                normal=(0, 0, -1), metadata={"description": "垫片底面"},
            ),
            create_axis_anchor(
                "center_axis", position=(0, 0, 0),
                direction=(0, 0, 1), metadata={"description": "中心轴线"},
            ),
        ]

    def build(self):
        p = self.params
        outer_r = p.outer_diameter / 2
        inner_r = p.inner_diameter / 2

        with BuildPart() as part:
            if p.washer_type == "spring":
                # Spring washer: ring with a gap (helical split)
                # Simplified: use a ring shape
                with BuildSketch() as s:
                    Circle(outer_r)
                extrude(amount=p.thickness)

                # Cut inner hole
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch() as s:
                        Circle(inner_r)
                    extrude(amount=p.thickness * 3, both=True)

                # Cut gap (split)
                gap_width = 0.8
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(outer_r - gap_width / 2, 0, 0)):
                        from build123d import Rectangle
                        Rectangle(gap_width, p.thickness * 0.6)
                    extrude(amount=outer_r * 2, both=True)

            elif p.washer_type == "lock":
                # Lock washer: internal teeth
                with BuildSketch() as s:
                    Circle(outer_r)
                extrude(amount=p.thickness)

                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch() as s:
                        Circle(inner_r)
                    extrude(amount=p.thickness * 3, both=True)

                # Tooth tabs bent inward (simplified: small bumps)
                import math
                for i in range(6):
                    angle = 2 * math.pi * i / 6
                    tx = (inner_r + 0.5) * math.cos(angle)
                    ty = (inner_r + 0.5) * math.sin(angle)
                    with BuildPart(mode=Mode.SUBTRACT):
                        with BuildSketch(Pos(tx, ty, 0)):
                            Circle(0.3)
                        extrude(amount=p.thickness * 3, both=True)

            else:
                # Flat washer
                with BuildSketch() as s:
                    Circle(outer_r)
                extrude(amount=p.thickness)

                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch() as s:
                        Circle(inner_r)
                    extrude(amount=p.thickness * 3, both=True)

        return part.part
