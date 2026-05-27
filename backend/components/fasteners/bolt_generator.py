"""Bolt generator - 六角螺栓、内六角、沉头螺丝。"""

from dataclasses import dataclass
from math import sqrt, pi, cos, sin
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle, RegularPolygon,
    extrude, Location, Pos, Mode, Axis,
)
from ...cad.base_part import BasePart, PartParams
from ...core.models import Anchor
from ...engineering.assembly.anchors import (
    create_face_anchor, create_axis_anchor, create_point_anchor,
)


# ISO 标准螺栓尺寸表 (diameter -> head dimensions)
HEX_HEAD_DIMS = {
    3: {"across_flats": 5.5, "height": 2.0},
    4: {"across_flats": 7.0, "height": 2.8},
    5: {"across_flats": 8.0, "height": 3.5},
    6: {"across_flats": 10.0, "height": 4.0},
    8: {"across_flats": 13.0, "height": 5.3},
    10: {"across_flats": 16.0, "height": 6.4},
    12: {"across_flats": 18.0, "height": 7.5},
    16: {"across_flats": 24.0, "height": 10.0},
    20: {"across_flats": 30.0, "height": 12.5},
}

SOCKET_HEAD_DIMS = {
    3: {"diameter": 5.5, "height": 3.0},
    4: {"diameter": 7.0, "height": 4.0},
    5: {"diameter": 8.5, "height": 5.0},
    6: {"diameter": 10.0, "height": 6.0},
    8: {"diameter": 13.0, "height": 8.0},
    10: {"diameter": 16.0, "height": 10.0},
    12: {"diameter": 18.0, "height": 12.0},
    16: {"diameter": 24.0, "height": 16.0},
    20: {"diameter": 30.0, "height": 20.0},
}


@dataclass
class BoltParams(PartParams):
    diameter: float = 6.0
    length: float = 20.0
    thread_pitch: float = 1.0
    head_type: str = "hex"          # hex, socket, flat
    strength_grade: str = "8.8"
    thread_length: float = 0.0      # 0 = auto (2.5 * diameter)


class Bolt(BasePart):
    def __init__(self, params: BoltParams):
        super().__init__(params)
        self.params = params

    def _get_head_dims(self) -> dict:
        d = int(self.params.diameter)
        if self.params.head_type == "hex":
            return HEX_HEAD_DIMS.get(d, {"across_flats": self.params.diameter * 1.8, "height": self.params.diameter * 0.7})
        elif self.params.head_type == "socket":
            return SOCKET_HEAD_DIMS.get(d, {"diameter": self.params.diameter * 1.6, "height": self.params.diameter})
        elif self.params.head_type == "flat":
            return {"diameter": self.params.diameter * 2.0, "height": self.params.diameter * 0.5}
        return HEX_HEAD_DIMS.get(d, {"across_flats": self.params.diameter * 1.8, "height": self.params.diameter * 0.7})

    def get_anchors(self) -> list[Anchor]:
        p = self.params
        dims = self._get_head_dims()
        head_h = dims["height"]
        return [
            create_face_anchor(
                "head_bottom", position=(0, 0, 0),
                normal=(0, 0, -1), metadata={"description": "螺栓头底面（装配面）"},
            ),
            create_axis_anchor(
                "shaft_axis", position=(0, 0, 0),
                direction=(0, 0, 1), metadata={"description": "螺栓轴线"},
            ),
            create_point_anchor(
                "tip", position=(0, 0, head_h + p.length),
                direction=(0, 0, 1), metadata={"description": "螺栓杆端"},
            ),
            create_point_anchor(
                "head_top", position=(0, 0, head_h),
                direction=(0, 0, 1), metadata={"description": "螺栓头顶面"},
            ),
        ]

    def build(self):
        p = self.params
        dims = self._get_head_dims()
        head_h = dims["height"]
        d = p.diameter

        with BuildPart() as part:
            # Head
            if p.head_type == "hex":
                # Hex head
                af = dims["across_flats"]
                circum_r = af / cos(pi / 6) / 2  # circumradius
                with BuildSketch() as s:
                    RegularPolygon(radius=circum_r, side_count=6)
                extrude(amount=head_h)

                # Chamfer top edge (simplified: smaller hex on top)
                chamfer_h = head_h * 0.15
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(0, 0, head_h - chamfer_h)):
                        Circle(circum_r * 0.15)
                    extrude(amount=chamfer_h + 1)

            elif p.head_type == "socket":
                # Socket head cap screw
                head_d = dims["diameter"]
                with BuildSketch() as s:
                    Circle(head_d / 2)
                extrude(amount=head_h)

                # Socket (hex recess)
                socket_r = d * 0.45
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(0, 0, head_h)):
                        RegularPolygon(radius=socket_r, side_count=6)
                    extrude(amount=head_h * 0.7)

            elif p.head_type == "flat":
                # Countersink flat head
                head_d = dims["diameter"]
                with BuildSketch() as s:
                    Circle(head_d / 2)
                extrude(amount=head_h)

                # Socket
                socket_r = d * 0.45
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(0, 0, head_h)):
                        RegularPolygon(radius=socket_r, side_count=6)
                    extrude(amount=head_h * 0.7)

            # Shank (shaft)
            with BuildSketch(Pos(0, 0, head_h)):
                Circle(d / 2)
            extrude(amount=p.length)

        return part.part
