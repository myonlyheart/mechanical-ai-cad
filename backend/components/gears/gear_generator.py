"""Gear generator - 直齿轮、斜齿轮、齿条。"""

from dataclasses import dataclass
from math import cos, sin, pi, tan
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle, RegularPolygon,
    extrude, Pos, Mode,
)
from ...cad.base_part import BasePart, PartParams
from ...core.models import Anchor
from ...engineering.assembly.anchors import (
    create_face_anchor, create_axis_anchor, create_point_anchor,
)


@dataclass
class GearParams(PartParams):
    module: float = 2.0
    tooth_count: int = 20
    pressure_angle: float = 20.0
    face_width: float = 10.0
    gear_type: str = "spur"         # spur, helical, rack
    helix_angle: float = 0.0        # degrees, for helical gears
    bore_diameter: float = 8.0
    keyway: bool = False
    rack_length: float = 100.0      # for rack type


class Gear(BasePart):
    def __init__(self, params: GearParams):
        super().__init__(params)
        self.params = params

    def _get_pitch_radius(self) -> float:
        return (self.params.module * self.params.tooth_count) / 2

    def _get_outer_radius(self) -> float:
        return self._get_pitch_radius() + self.params.module

    def _get_root_radius(self) -> float:
        return self._get_pitch_radius() - 1.25 * self.params.module

    def get_anchors(self) -> list[Anchor]:
        p = self.params
        anchors = [
            create_axis_anchor(
                "gear_center", position=(0, 0, 0),
                direction=(0, 0, 1), metadata={"description": "齿轮中心轴线"},
            ),
            create_face_anchor(
                "face_left", position=(0, 0, 0),
                normal=(0, 0, -1), metadata={"description": "左端面"},
            ),
            create_face_anchor(
                "face_right", position=(0, 0, p.face_width),
                normal=(0, 0, 1), metadata={"description": "右端面"},
            ),
        ]
        if p.bore_diameter > 0:
            anchors.append(create_face_anchor(
                "bore_face", position=(p.bore_diameter / 2, 0, p.face_width / 2),
                normal=(1, 0, 0), metadata={"description": "内孔面"},
            ))
        return anchors

    def build(self):
        p = self.params

        if p.gear_type == "rack":
            return self._build_rack()

        outer_r = self._get_outer_radius()
        root_r = self._get_root_radius()
        pitch_r = self._get_pitch_radius()
        # tooth angular width
        tooth_angle = 2 * pi / p.tooth_count

        with BuildPart() as part:
            # Gear body (outer circle)
            with BuildSketch():
                Circle(outer_r)
            extrude(amount=p.face_width)

            # Tooth profile approximation: cut between teeth
            # Use root radius cuts to create tooth shapes
            tooth_half_width = tooth_angle * 0.4
            for i in range(p.tooth_count):
                angle = tooth_angle * i
                # Cut gap between teeth
                gap_start = angle + tooth_half_width
                gap_end = angle + tooth_angle - tooth_half_width
                mid_angle = (gap_start + gap_end) / 2
                gx = root_r * 0.95 * cos(mid_angle)
                gy = root_r * 0.95 * sin(mid_angle)
                gap_width = (gap_end - gap_start) * outer_r * 0.15

                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(gx, gy, 0)):
                        from build123d import Rectangle as Rect
                        Rect(gap_width, (outer_r - root_r) * 1.2)
                    extrude(amount=p.face_width * 2, both=True)

            # Center bore
            if p.bore_diameter > 0:
                bore_r = p.bore_diameter / 2
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch():
                        Circle(bore_r)
                    extrude(amount=p.face_width * 2, both=True)

                # Keyway
                if p.keyway:
                    kw_w = p.bore_diameter * 0.25
                    kw_d = p.bore_diameter * 0.125
                    with BuildPart(mode=Mode.SUBTRACT):
                        with BuildSketch(Pos(0, bore_r + kw_d / 2, 0)):
                            from build123d import Rectangle as Rect
                            Rect(kw_w, kw_d)
                        extrude(amount=p.face_width * 2, both=True)

        return part.part

    def _build_rack(self):
        """Build a rack (linear gear)."""
        p = self.params
        pitch = pi * p.module
        tooth_h = 2.25 * p.module
        tooth_w = pitch * 0.5
        num_teeth = int(p.rack_length / pitch)
        base_width = p.face_width

        with BuildPart() as part:
            # Base bar
            with BuildSketch():
                Rectangle(p.rack_length, tooth_h)
            extrude(amount=base_width)

            # Teeth (raised rectangles)
            for i in range(num_teeth):
                x = -p.rack_length / 2 + pitch * 0.25 + i * pitch
                with BuildSketch(Pos(x, tooth_h / 2, 0)):
                    from build123d import Rectangle as Rect
                    Rect(tooth_w, p.module * 1.2)
                extrude(amount=base_width)

            # Mounting holes
            hole_spacing = p.rack_length / (num_teeth + 1)
            for i in range(min(num_teeth, 6)):
                x = -p.rack_length / 2 + hole_spacing * (i + 1)
                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(x, 0, 0)):
                        Circle(p.module * 1.5)
                    extrude(amount=base_width * 2, both=True)

        return part.part
