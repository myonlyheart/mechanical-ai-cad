"""Anchor 系统 - 定义零件上的可连接位置。

支持类型: point, face, edge, axis, hole_center
自动生成局部坐标，供装配和 Three.js 可视化使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.models import Anchor


# 锚点类型常量
ANCHOR_POINT = "point"
ANCHOR_FACE = "face"
ANCHOR_EDGE = "edge"
ANCHOR_AXIS = "axis"
ANCHOR_HOLE_CENTER = "hole_center"

ANCHOR_TYPES = [ANCHOR_POINT, ANCHOR_FACE, ANCHOR_EDGE, ANCHOR_AXIS, ANCHOR_HOLE_CENTER]


def create_point_anchor(
    name: str,
    position: tuple[float, float, float],
    direction: tuple[float, float, float] = (0.0, 0.0, 1.0),
    metadata: dict[str, Any] | None = None,
) -> Anchor:
    """创建点锚点。"""
    return Anchor(
        name=name, type=ANCHOR_POINT,
        position=position, direction=direction,
        metadata=metadata or {},
    )


def create_face_anchor(
    name: str,
    position: tuple[float, float, float],
    normal: tuple[float, float, float] = (0.0, 0.0, 1.0),
    metadata: dict[str, Any] | None = None,
) -> Anchor:
    """创建面锚点。"""
    return Anchor(
        name=name, type=ANCHOR_FACE,
        position=position, direction=normal,
        metadata=metadata or {},
    )


def create_axis_anchor(
    name: str,
    position: tuple[float, float, float],
    direction: tuple[float, float, float] = (0.0, 0.0, 1.0),
    metadata: dict[str, Any] | None = None,
) -> Anchor:
    """创建轴锚点。"""
    return Anchor(
        name=name, type=ANCHOR_AXIS,
        position=position, direction=direction,
        metadata=metadata or {},
    )


def create_hole_center_anchor(
    name: str,
    position: tuple[float, float, float],
    direction: tuple[float, float, float] = (0.0, 0.0, 1.0),
    diameter: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> Anchor:
    """创建孔中心锚点。"""
    meta = metadata or {}
    meta["diameter"] = diameter
    return Anchor(
        name=name, type=ANCHOR_HOLE_CENTER,
        position=position, direction=direction,
        metadata=meta,
    )


def create_edge_anchor(
    name: str,
    position: tuple[float, float, float],
    direction: tuple[float, float, float] = (0.0, 0.0, 1.0),
    metadata: dict[str, Any] | None = None,
) -> Anchor:
    """创建边锚点。"""
    return Anchor(
        name=name, type=ANCHOR_EDGE,
        position=position, direction=direction,
        metadata=metadata or {},
    )


# ============================================================
# 预定义零件锚点模板
# ============================================================

def nema17_mount_anchors(
    base_length: float = 60,
    base_width: float = 60,
    mount_height: float = 40,
    motor_hole_spacing: float = 31.0,
    center_bore: float = 22.0,
) -> list[Anchor]:
    """NEMA17 电机支架默认锚点。"""
    half = motor_hole_spacing / 2
    bore_y = -base_width / 2 + mount_height / 2
    return [
        create_face_anchor(
            "mount_face", position=(0, bore_y, 0),
            normal=(0, 0, 1), metadata={"description": "电机安装面"},
        ),
        create_axis_anchor(
            "shaft_axis", position=(0, bore_y, 0),
            direction=(0, 0, 1), metadata={"description": "电机轴线"},
        ),
        create_hole_center_anchor(
            "motor_hole_1", position=(half, bore_y + half, 0),
            direction=(0, 0, 1), diameter=4.0,
        ),
        create_hole_center_anchor(
            "motor_hole_2", position=(half, bore_y - half, 0),
            direction=(0, 0, 1), diameter=4.0,
        ),
        create_hole_center_anchor(
            "motor_hole_3", position=(-half, bore_y + half, 0),
            direction=(0, 0, 1), diameter=4.0,
        ),
        create_hole_center_anchor(
            "motor_hole_4", position=(-half, bore_y - half, 0),
            direction=(0, 0, 1), diameter=4.0,
        ),
        create_face_anchor(
            "base_face", position=(0, 0, 0),
            normal=(0, 0, -1), metadata={"description": "底座安装面"},
        ),
    ]


def l_bracket_anchors(
    length: float = 80,
    width: float = 40,
    height: float = 60,
    thickness: float = 5,
    hole_diameter: float = 6.5,
) -> list[Anchor]:
    """L 型支架默认锚点。"""
    return [
        create_face_anchor(
            "vertical_face", position=(0, 0, thickness / 2),
            normal=(0, 0, 1), metadata={"description": "垂直安装面"},
        ),
        create_face_anchor(
            "horizontal_face", position=(0, 0, -thickness / 2),
            normal=(0, 0, -1), metadata={"description": "水平安装面"},
        ),
        create_hole_center_anchor(
            "v_hole_top", position=(0, height / 4, thickness / 2),
            direction=(0, 0, 1), diameter=hole_diameter,
        ),
        create_hole_center_anchor(
            "v_hole_bottom", position=(0, -height / 4, thickness / 2),
            direction=(0, 0, 1), diameter=hole_diameter,
        ),
        create_hole_center_anchor(
            "h_hole_left", position=(length / 4, 0, -thickness / 2),
            direction=(0, 0, -1), diameter=hole_diameter,
        ),
        create_hole_center_anchor(
            "h_hole_right", position=(-length / 4, 0, -thickness / 2),
            direction=(0, 0, -1), diameter=hole_diameter,
        ),
    ]


def t_bracket_anchors(
    length: float = 100,
    width: float = 50,
    height: float = 60,
    thickness: float = 5,
    hole_diameter: float = 6.5,
) -> list[Anchor]:
    """T 型支架默认锚点。"""
    return [
        create_face_anchor(
            "vertical_face", position=(0, 0, thickness / 2),
            normal=(0, 0, 1), metadata={"description": "垂直安装面"},
        ),
        create_face_anchor(
            "horizontal_face", position=(0, 0, -thickness / 2),
            normal=(0, 0, -1), metadata={"description": "水平安装面"},
        ),
        create_hole_center_anchor(
            "h_hole_left", position=(length / 4, 0, -thickness / 2),
            direction=(0, 0, -1), diameter=hole_diameter,
        ),
        create_hole_center_anchor(
            "h_hole_right", position=(-length / 4, 0, -thickness / 2),
            direction=(0, 0, -1), diameter=hole_diameter,
        ),
    ]


def bearing_block_anchors(
    base_length: float = 60,
    base_width: float = 40,
    height: float = 30,
    bearing_diameter: float = 22,
    mounting_hole_spacing: float = 45,
) -> list[Anchor]:
    """轴承座默认锚点。"""
    return [
        create_axis_anchor(
            "bearing_axis", position=(0, 0, height),
            direction=(1, 0, 0), metadata={"description": "轴承轴线"},
        ),
        create_face_anchor(
            "base_face", position=(0, 0, 0),
            normal=(0, 0, -1), metadata={"description": "底座安装面"},
        ),
        create_hole_center_anchor(
            "mount_hole_left", position=(-mounting_hole_spacing / 2, 0, 0),
            direction=(0, 0, -1), diameter=5.0,
        ),
        create_hole_center_anchor(
            "mount_hole_right", position=(mounting_hole_spacing / 2, 0, 0),
            direction=(0, 0, -1), diameter=5.0,
        ),
    ]


def flange_anchors(
    outer_diameter: float = 80,
    bore_diameter: float = 30,
    thickness: float = 8,
    bolt_circle_diameter: float = 68,
    bolt_count: int = 6,
    bolt_hole_diameter: float = 8,
) -> list[Anchor]:
    """法兰默认锚点。"""
    import math
    bolt_r = bolt_circle_diameter / 2
    anchors = [
        create_axis_anchor(
            "center_axis", position=(0, 0, 0),
            direction=(0, 0, 1), metadata={"description": "中心轴线"},
        ),
        create_face_anchor(
            "face_front", position=(0, 0, thickness),
            normal=(0, 0, 1), metadata={"description": "前端面"},
        ),
        create_face_anchor(
            "face_back", position=(0, 0, 0),
            normal=(0, 0, -1), metadata={"description": "后端面"},
        ),
    ]
    for i in range(bolt_count):
        angle = 2 * math.pi * i / bolt_count
        x = bolt_r * math.cos(angle)
        y = bolt_r * math.sin(angle)
        anchors.append(create_hole_center_anchor(
            f"bolt_hole_{i + 1}", position=(x, y, thickness / 2),
            direction=(0, 0, 1), diameter=bolt_hole_diameter,
        ))
    return anchors


def coupling_anchors(
    outer_diameter: float = 30,
    length: float = 40,
    bore_diameter: float = 8,
) -> list[Anchor]:
    """联轴器默认锚点。"""
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
            "face_right", position=(0, 0, length),
            normal=(0, 0, 1), metadata={"description": "右端面"},
        ),
        create_hole_center_anchor(
            "bore_left", position=(0, 0, 0),
            direction=(0, 0, -1), diameter=bore_diameter,
        ),
        create_hole_center_anchor(
            "bore_right", position=(0, 0, length),
            direction=(0, 0, 1), diameter=bore_diameter,
        ),
    ]


def shaft_sleeve_anchors(
    outer_diameter: float = 20,
    inner_diameter: float = 12,
    length: float = 30,
    flange_diameter: float = 28,
    flange_thickness: float = 3,
) -> list[Anchor]:
    """轴套默认锚点。"""
    return [
        create_axis_anchor(
            "axis", position=(0, 0, 0),
            direction=(0, 0, 1), metadata={"description": "中心轴线"},
        ),
        create_face_anchor(
            "face_front", position=(0, 0, flange_thickness + length),
            normal=(0, 0, 1), metadata={"description": "前端面"},
        ),
        create_face_anchor(
            "face_back", position=(0, 0, flange_thickness),
            normal=(0, 0, -1), metadata={"description": "后端面（凸缘侧）"},
        ),
        create_face_anchor(
            "flange_face", position=(0, 0, 0),
            normal=(0, 0, -1), metadata={"description": "凸缘底面"},
        ),
    ]
