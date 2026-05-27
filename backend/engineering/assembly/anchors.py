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
