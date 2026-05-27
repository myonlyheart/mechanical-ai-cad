"""Nut generator - 六角螺母、法兰螺母、锁紧螺母。"""

from dataclasses import dataclass
from math import cos, pi
from build123d import (
    BuildPart, BuildSketch, Circle, RegularPolygon,
    extrude, Pos, Mode,
)
from ...cad.base_part import BasePart, PartParams
from ...core.models import Anchor
from ...engineering.assembly.anchors import (
    create_face_anchor, create_axis_anchor, create_hole_center_anchor,
)

# ISO 标准螺母尺寸
NUT_DIMS = {
    3: {"across_flats": 5.5, "height": 2.4},
    4: {"across_flats": 7.0, "height": 3.2},
    5: {"across_flats": 8.0, "height": 4.7},
    6: {"across_flats": 10.0, "height": 5.2},
    8: {"across_flats": 13.0, "height": 6.8},
    10: {"across_flats": 16.0, "height": 8.4},
    12: {"across_flats": 18.0, "height": 10.8},
    16: {"across_flats": 24.0, "height": 14.8},
    20: {"across_flats": 30.0, "height": 18.0},
}


@dataclass
class NutParams(PartParams):
    diameter: float = 6.0
    nut_type: str = "hex"           # hex, flange, nylock
    height: float = 0.0             # 0 = use standard
    thread_pitch: float = 1.0


class Nut(BasePart):
    def __init__(self, params: NutParams):
        super().__init__(params)
        self.params = params

    def _get_dims(self) -> dict:
        d = int(self.params.diameter)
        return NUT_DIMS.get(d, {"across_flats": self.params.diameter * 1.8, "height": self.params.diameter * 0.8})

    def get_anchors(self) -> list[Anchor]:
        dims = self._get_dims()
        h = self.params.height or dims["height"]
        return [
            create_face_anchor(
                "top_face", position=(0, 0, h),
                normal=(0, 0, 1), metadata={"description": "螺母顶面"},
            ),
            create_face_anchor(
                "bottom_face", position=(0, 0, 0),
                normal=(0, 0, -1), metadata={"description": "螺母底面"},
            ),
            create_axis_anchor(
                "thread_axis", position=(0, 0, 0),
                direction=(0, 0, 1), metadata={"description": "螺纹轴线"},
            ),
        ]

    def build(self):
        p = self.params
        dims = self._get_dims()
        h = p.height or dims["height"]
        af = dims["across_flats"]
        circum_r = af / cos(pi / 6) / 2
        bore_r = p.diameter / 2

        with BuildPart() as part:
            if p.nut_type == "flange":
                # Flange nut: hex body + wider flange base
                flange_r = circum_r * 1.4
                flange_h = h * 0.2

                # Flange base
                with BuildSketch() as s:
                    Circle(flange_r)
                extrude(amount=flange_h)

                # Hex body on top
                with BuildSketch(Pos(0, 0, flange_h)) as s:
                    RegularPolygon(radius=circum_r, side_count=6)
                extrude(amount=h - flange_h)

            elif p.nut_type == "nylock":
                # Nylock nut: hex body + nylon insert ring at top
                with BuildSketch() as s:
                    RegularPolygon(radius=circum_r, side_count=6)
                extrude(amount=h)

                # Nylon insert ring (solid at top to "lock")
                insert_h = h * 0.3
                with BuildSketch(Pos(0, 0, h - insert_h)) as s:
                    Circle(bore_r + 0.5)
                extrude(amount=insert_h)

            else:
                # Standard hex nut
                with BuildSketch() as s:
                    RegularPolygon(radius=circum_r, side_count=6)
                extrude(amount=h)

            # Thread bore
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch() as s:
                    Circle(bore_r)
                extrude(amount=h * 3, both=True)

        return part.part
