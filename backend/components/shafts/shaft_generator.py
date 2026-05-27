"""Shaft generator - 圆轴、台阶轴、键槽轴、螺纹轴。"""

from dataclasses import dataclass, field
from build123d import (
    BuildPart, BuildSketch, Circle, Rectangle,
    extrude, Pos, Mode, RegularPolygon,
)
from ...cad.base_part import BasePart, PartParams
from ...core.models import Anchor
from ...engineering.assembly.anchors import (
    create_face_anchor, create_axis_anchor, create_point_anchor,
)


@dataclass
class ShaftParams(PartParams):
    diameter: float = 8.0
    length: float = 120.0
    shaft_type: str = "round"       # round, stepped, keyed, threaded
    steps: list = field(default_factory=list)   # [(diameter, length), ...] for stepped
    keyway_width: float = 0.0       # 0 = no keyway
    keyway_depth: float = 0.0
    keyway_length: float = 0.0
    keyway_offset: float = 0.0      # keyway distance from left end
    thread_length: float = 0.0      # 0 = no thread
    thread_pitch: float = 1.5
    chamfer: float = 0.5


class Shaft(BasePart):
    def __init__(self, params: ShaftParams):
        super().__init__(params)
        self.params = params

    def get_anchors(self) -> list[Anchor]:
        p = self.params
        anchors = [
            create_axis_anchor(
                "axis", position=(0, 0, 0),
                direction=(0, 0, 1), metadata={"description": "轴线"},
            ),
            create_face_anchor(
                "face_left", position=(0, 0, 0),
                normal=(0, 0, -1), metadata={"description": "左端面"},
            ),
            create_face_anchor(
                "face_right", position=(0, 0, p.length),
                normal=(0, 0, 1), metadata={"description": "右端面"},
            ),
        ]

        if p.shaft_type == "keyed" and p.keyway_width > 0:
            kw_offset = p.keyway_offset or p.length * 0.3
            anchors.append(create_face_anchor(
                "keyway_top",
                position=(0, p.diameter / 2 - p.keyway_depth / 2, kw_offset + p.keyway_length / 2),
                normal=(0, 1, 0), metadata={"description": "键槽顶面"},
            ))

        if p.shaft_type == "threaded" and p.thread_length > 0:
            anchors.append(create_point_anchor(
                "thread_start", position=(0, 0, p.length - p.thread_length),
                direction=(0, 0, 1), metadata={"description": "螺纹起始"},
            ))

        if p.shaft_type == "stepped" and p.steps:
            z = 0
            for i, (step_d, step_l) in enumerate(p.steps):
                z += step_l
                anchors.append(create_face_anchor(
                    f"step_{i + 1}_face", position=(0, 0, z),
                    normal=(0, 0, 1), metadata={"description": f"台阶 {i + 1} 端面"},
                ))

        return anchors

    def build(self):
        p = self.params

        with BuildPart() as part:
            if p.shaft_type == "stepped" and p.steps:
                # Stepped shaft: multiple cylinders
                z = 0
                for step_d, step_l in p.steps:
                    with BuildSketch(Pos(0, 0, z)):
                        Circle(step_d / 2)
                    extrude(amount=step_l)
                    z += step_l

            elif p.shaft_type == "keyed":
                # Round shaft with keyway
                with BuildSketch():
                    Circle(p.diameter / 2)
                extrude(amount=p.length)

                # Keyway
                kw_w = p.keyway_width or p.diameter * 0.25
                kw_d = p.keyway_depth or p.diameter * 0.125
                kw_l = p.keyway_length or p.length * 0.4
                kw_offset = p.keyway_offset or p.length * 0.3
                kw_y = p.diameter / 2 - kw_d / 2

                with BuildPart(mode=Mode.SUBTRACT):
                    with BuildSketch(Pos(0, kw_y, kw_offset + kw_l / 2)):
                        Rectangle(kw_w, kw_d)
                    extrude(amount=kw_l)

            elif p.shaft_type == "threaded":
                # Round shaft with threaded section
                with BuildSketch():
                    Circle(p.diameter / 2)
                extrude(amount=p.length)

                # Thread representation: grooved cylinder
                thread_d = p.diameter - p.thread_pitch * 0.6
                if p.thread_length > 0 and thread_d > 0:
                    with BuildSketch(Pos(0, 0, p.length - p.thread_length)):
                        Circle(thread_d / 2)
                    extrude(amount=p.thread_length)

                    # Helical grooves (simplified: 4 flat cuts)
                    groove_w = p.thread_pitch * 0.3
                    import math
                    for i in range(4):
                        angle = math.pi * i / 2
                        gx = (p.diameter / 2) * math.cos(angle)
                        gy = (p.diameter / 2) * math.sin(angle)
                        with BuildPart(mode=Mode.SUBTRACT):
                            with BuildSketch(Pos(gx * 0.6, gy * 0.6, p.length - p.thread_length)):
                                Circle(groove_w / 2)
                            extrude(amount=p.thread_length)

            else:
                # Round shaft (default)
                with BuildSketch():
                    Circle(p.diameter / 2)
                extrude(amount=p.length)

            # Chamfer ends
            if p.chamfer > 0:
                chamfer_r = p.diameter / 2 - p.chamfer
                if chamfer_r > 0:
                    # Left end chamfer
                    with BuildPart(mode=Mode.SUBTRACT):
                        with BuildSketch():
                            Circle(p.diameter / 2)
                        with BuildSketch(Pos(0, 0, 0)):
                            Circle(chamfer_r)
                        extrude(amount=p.chamfer)

                    # Right end chamfer
                    with BuildPart(mode=Mode.SUBTRACT):
                        with BuildSketch():
                            Circle(p.diameter / 2)
                        with BuildSketch(Pos(0, 0, p.length - p.chamfer)):
                            Circle(chamfer_r)
                        extrude(amount=p.chamfer)

        return part.part
