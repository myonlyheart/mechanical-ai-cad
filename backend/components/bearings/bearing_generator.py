"""Bearing generator - 深沟球轴承、法兰轴承、推力轴承。"""

from dataclasses import dataclass
from math import cos, sin, pi
from build123d import (
    BuildPart, BuildSketch, Circle, RegularPolygon,
    extrude, Pos, Mode,
)
from ...cad.base_part import BasePart, PartParams
from ...core.models import Anchor
from ...engineering.assembly.anchors import (
    create_face_anchor, create_axis_anchor, create_face_anchor,
)

# 常用轴承系列尺寸
BEARING_SERIES_DIMS = {
    "6000": {"id": 10, "od": 26, "width": 8},
    "6001": {"id": 12, "od": 28, "width": 8},
    "6002": {"id": 15, "od": 32, "width": 9},
    "6003": {"id": 17, "od": 35, "width": 10},
    "6004": {"id": 20, "od": 42, "width": 12},
    "6005": {"id": 25, "od": 47, "width": 12},
    "6006": {"id": 30, "od": 55, "width": 13},
    "6007": {"id": 35, "od": 62, "width": 14},
    "6008": {"id": 40, "od": 68, "width": 15},
    "6009": {"id": 45, "od": 75, "width": 16},
    "6010": {"id": 50, "od": 80, "width": 16},
    "6200": {"id": 10, "od": 30, "width": 9},
    "6201": {"id": 12, "od": 32, "width": 10},
    "6202": {"id": 15, "od": 35, "width": 11},
    "6203": {"id": 17, "od": 40, "width": 12},
    "6204": {"id": 20, "od": 47, "width": 14},
    "6205": {"id": 25, "od": 52, "width": 15},
    "6206": {"id": 30, "od": 62, "width": 16},
    "6207": {"id": 35, "od": 72, "width": 17},
    "6208": {"id": 40, "od": 80, "width": 18},
    "6209": {"id": 45, "od": 85, "width": 19},
    "6210": {"id": 50, "od": 90, "width": 20},
}


@dataclass
class BearingParams(PartParams):
    inner_diameter: float = 8.0
    outer_diameter: float = 22.0
    width: float = 7.0
    bearing_type: str = "deep_groove"   # deep_groove, flanged, thrust
    series: str = ""                     # e.g. "6205" - auto-fills dimensions
    seal_type: str = "open"              # open, sealed, shielded


class Bearing(BasePart):
    def __init__(self, params: BearingParams):
        super().__init__(params)
        self.params = params
        # Auto-fill from series if specified
        if params.series and params.series in BEARING_SERIES_DIMS:
            dims = BEARING_SERIES_DIMS[params.series]
            if params.inner_diameter == 8.0:  # only override defaults
                self.params.inner_diameter = dims["id"]
            if params.outer_diameter == 22.0:
                self.params.outer_diameter = dims["od"]
            if params.width == 7.0:
                self.params.width = dims["width"]

    def get_anchors(self) -> list[Anchor]:
        p = self.params
        return [
            create_axis_anchor(
                "axis", position=(0, 0, 0),
                direction=(0, 0, 1), metadata={"description": "中心轴线"},
            ),
            create_face_anchor(
                "face_left", position=(0, 0, 0),
                normal=(0, 0, -1), metadata={"description": "左端面"},
            ),
            create_face_anchor(
                "face_right", position=(0, 0, p.width),
                normal=(0, 0, 1), metadata={"description": "右端面"},
            ),
            create_face_anchor(
                "inner_bore", position=(p.inner_diameter / 2, 0, p.width / 2),
                normal=(1, 0, 0), metadata={"description": "内孔面"},
            ),
            create_face_anchor(
                "outer_race", position=(p.outer_diameter / 2, 0, p.width / 2),
                normal=(1, 0, 0), metadata={"description": "外圈面"},
            ),
        ]

    def build(self):
        p = self.params
        inner_r = p.inner_diameter / 2
        outer_r = p.outer_diameter / 2
        mid_r = (inner_r + outer_r) / 2
        groove_r = (outer_r - inner_r) * 0.35  # ball groove depth

        with BuildPart() as part:
            if p.bearing_type == "thrust":
                # Thrust bearing: two flat washers with ball race
                # Bottom washer
                with BuildSketch() as s:
                    Circle(outer_r)
                extrude(amount=p.width * 0.35)

                # Top washer
                with BuildSketch(Pos(0, 0, p.width * 0.65)) as s:
                    Circle(outer_r)
                extrude(amount=p.width * 0.35)

                # Ball race ring (visual)
                race_h = p.width * 0.3
                with BuildSketch(Pos(0, 0, p.width * 0.35)) as s:
                    Circle(outer_r * 0.95)
                with BuildSketch(Pos(0, 0, p.width * 0.35)) as s:
                    Circle(inner_r * 1.1)
                extrude(amount=race_h)

            elif p.bearing_type == "flanged":
                # Flanged bearing: deep groove + flange at one end
                flange_od = outer_r * 1.3
                flange_h = p.width * 0.15

                # Main bearing body
                with BuildSketch() as s:
                    Circle(outer_r)
                extrude(amount=p.width)

                # Flange
                with BuildSketch(Pos(0, 0, 0)) as s:
                    Circle(flange_od)
                extrude(amount=flange_h)

                # Inner bore
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch() as s:
                        Circle(inner_r)
                    extrude(amount=p.width * 3, both=True)

                # Ball groove (outer raceway)
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(0, 0, p.width / 2)) as s:
                        Circle(mid_r + groove_r)
                    extrude(amount=p.width * 0.5)

                # Inner raceway
                with BuildSketch(Pos(0, 0, 0)) as s:
                    Circle(mid_r - groove_r * 0.5)
                extrude(amount=p.width)

            else:
                # Deep groove ball bearing (default)
                # Outer ring
                with BuildSketch() as s:
                    Circle(outer_r)
                extrude(amount=p.width)

                # Inner bore
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch() as s:
                        Circle(inner_r)
                    extrude(amount=p.width * 3, both=True)

                # Ball groove (outer raceway channel)
                groove_depth = groove_r
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(0, 0, p.width / 2)) as s:
                        Circle(mid_r + groove_depth)
                    extrude(amount=p.width * 0.6)

                # Inner race lip (raised inner ring edge)
                inner_lip_r = inner_r + (mid_r - inner_r) * 0.3
                with BuildSketch(Pos(0, 0, 0)) as s:
                    Circle(inner_lip_r)
                extrude(amount=p.width)

                # Balls (visual representation)
                ball_r = groove_r * 0.7
                num_balls = max(6, int(2 * pi * mid_r / (ball_r * 3)))
                for i in range(num_balls):
                    angle = 2 * pi * i / num_balls
                    bx = mid_r * cos(angle)
                    by = mid_r * sin(angle)
                    with BuildPart(mode=Mode.SUBTRACT):
                        with BuildSketch(Pos(bx, by, p.width / 2)) as s:
                            Circle(ball_r * 0.3)  # small hole as ball marker
                        extrude(amount=p.width * 0.4)

                # Seal/shield (if not open)
                if p.seal_type in ("sealed", "shielded"):
                    seal_h = p.width * 0.1
                    with BuildSketch(Pos(0, 0, 0)) as s:
                        Circle(outer_r - 0.2)
                    with BuildSketch(Pos(0, 0, 0)) as s:
                        Circle(inner_r + 0.2)
                    extrude(amount=seal_h)

                    with BuildSketch(Pos(0, 0, p.width - seal_h)) as s:
                        Circle(outer_r - 0.2)
                    with BuildSketch(Pos(0, 0, p.width - seal_h)) as s:
                        Circle(inner_r + 0.2)
                    extrude(amount=seal_h)

        return part.part
