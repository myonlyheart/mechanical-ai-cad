"""约束求解器 - 支持多种工程约束类型。

支持：coincident, parallel, perpendicular, tangent, distance, angle
支持自然语言："左右对称"、"孔居中" → 自动生成 Constraint
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from ...core.models import Anchor


@dataclass
class Constraint:
    """工程约束定义。"""
    id: str = ""
    type: str = ""           # coincident | parallel | perpendicular | tangent | distance | angle
    source_anchor: str = ""
    target_anchor: str = ""
    value: float = 0.0       # 距离值 / 角度值
    solved: bool = False
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


# ============================================================
# 约束求解函数
# ============================================================

def solve_coincident(src: Anchor, tgt: Anchor) -> dict[str, Any]:
    """求解重合约束。"""
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]
    return {
        "valid": True,
        "translation": (dx, dy, dz),
        "rotation": (0, 0, 0),
        "message": f"重合约束: 平移 ({dx:.2f}, {dy:.2f}, {dz:.2f})",
    }


def solve_parallel(src: Anchor, tgt: Anchor) -> dict[str, Any]:
    """求解平行约束。"""
    dot = (
        src.direction[0] * tgt.direction[0]
        + src.direction[1] * tgt.direction[1]
        + src.direction[2] * tgt.direction[2]
    )
    is_parallel = abs(abs(dot) - 1.0) < 0.01
    return {
        "valid": is_parallel,
        "translation": (0, 0, 0),
        "rotation": (0, 0, 0),
        "message": "方向已平行" if is_parallel else "需要旋转对齐方向",
    }


def solve_perpendicular(src: Anchor, tgt: Anchor) -> dict[str, Any]:
    """求解垂直约束。"""
    dot = (
        src.direction[0] * tgt.direction[0]
        + src.direction[1] * tgt.direction[1]
        + src.direction[2] * tgt.direction[2]
    )
    is_perp = abs(dot) < 0.01
    return {
        "valid": is_perp,
        "translation": (0, 0, 0),
        "rotation": (0, 0, 0),
        "message": "方向已垂直" if is_perp else "需要旋转使方向垂直",
    }


def solve_distance(src: Anchor, tgt: Anchor, distance: float) -> dict[str, Any]:
    """求解距离约束。"""
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]
    current = math.sqrt(dx * dx + dy * dy + dz * dz)

    if current < 1e-6:
        return {"valid": False, "message": "锚点重合，无法计算距离"}

    factor = distance / current
    return {
        "valid": True,
        "translation": (dx * factor - dx, dy * factor - dy, dz * factor - dz),
        "rotation": (0, 0, 0),
        "message": f"距离约束: {current:.2f}mm → {distance:.2f}mm",
    }


def solve_angle(src: Anchor, tgt: Anchor, angle_deg: float) -> dict[str, Any]:
    """求解角度约束。"""
    dot = (
        src.direction[0] * tgt.direction[0]
        + src.direction[1] * tgt.direction[1]
        + src.direction[2] * tgt.direction[2]
    )
    current_angle = math.degrees(math.acos(max(-1, min(1, dot))))
    return {
        "valid": abs(current_angle - angle_deg) < 0.5,
        "translation": (0, 0, 0),
        "rotation": (0, 0, 0),
        "message": f"角度约束: 当前 {current_angle:.1f}°, 目标 {angle_deg:.1f}°",
    }


def solve_tangent(src: Anchor, tgt: Anchor) -> dict[str, Any]:
    """求解相切约束（简化版）。"""
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]
    return {
        "valid": True,
        "translation": (dx, dy, dz),
        "rotation": (0, 0, 0),
        "message": "相切约束: 对齐到切点",
    }


# 求解器路由表
SOLVERS = {
    "coincident": solve_coincident,
    "parallel": solve_parallel,
    "perpendicular": solve_perpendicular,
    "distance": solve_distance,
    "angle": solve_angle,
    "tangent": solve_tangent,
}


def solve_constraint(
    constraint: Constraint,
    source_anchor: Anchor,
    target_anchor: Anchor,
) -> dict[str, Any]:
    """求解单个约束。"""
    solver = SOLVERS.get(constraint.type)
    if solver is None:
        return {"valid": False, "message": f"不支持的约束类型: {constraint.type}"}

    if constraint.type in ("distance", "angle"):
        return solver(source_anchor, target_anchor, constraint.value)
    return solver(source_anchor, target_anchor)


# ============================================================
# 自然语言 → 约束映射
# ============================================================

NL_CONSTRAINT_PATTERNS = {
    "左右对称": lambda parts: [
        Constraint(type="parallel", source_anchor="center", target_anchor="center"),
    ],
    "孔居中": lambda parts: [
        Constraint(type="coincident", source_anchor="hole_center", target_anchor="center"),
    ],
    "对齐": lambda parts: [
        Constraint(type="coincident", source_anchor="face", target_anchor="face"),
    ],
    "平行": lambda parts: [
        Constraint(type="parallel", source_anchor="axis", target_anchor="axis"),
    ],
    "垂直": lambda parts: [
        Constraint(type="perpendicular", source_anchor="axis", target_anchor="axis"),
    ],
}


def parse_nl_constraints(text: str, parts: list[dict] | None = None) -> list[Constraint]:
    """从自然语言解析约束。

    Args:
        text: 用户描述（如 "左右对称"、"孔居中"）
        parts: 零件列表（可选）

    Returns:
        约束列表
    """
    constraints: list[Constraint] = []
    for keyword, generator in NL_CONSTRAINT_PATTERNS.items():
        if keyword in text:
            constraints.extend(generator(parts or []))
    return constraints
