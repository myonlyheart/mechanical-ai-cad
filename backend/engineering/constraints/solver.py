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
    type: str = ""           # coincident | parallel | perpendicular | tangent | distance | angle | gear_mesh | slider | rotational
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
    """求解相切约束。将源点沿法线方向移动到切点位置。

    src: 圆/球面上的锚点（direction = 法线方向）
    tgt: 目标面/线的锚点（direction = 法线/切线方向）
    """
    # 源点沿其法线方向投射到目标位置
    # 简化：将源点移动到目标位置（方向已在各自的 direction 中编码）
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]

    # 如果两个方向已对齐（反向），说明已经在切点
    dot = (
        src.direction[0] * tgt.direction[0]
        + src.direction[1] * tgt.direction[1]
        + src.direction[2] * tgt.direction[2]
    )
    is_tangent = abs(dot) < 0.1  # 法线垂直 = 相切

    if is_tangent:
        return {
            "valid": True,
            "translation": (dx, dy, dz),
            "rotation": (0, 0, 0),
            "message": "相切约束: 已相切",
        }

    # 计算需要沿目标法线方向移动的距离
    proj = dx * tgt.direction[0] + dy * tgt.direction[1] + dz * tgt.direction[2]
    tx = dx - proj * tgt.direction[0]
    ty = dy - proj * tgt.direction[1]
    tz = dz - proj * tgt.direction[2]
    return {
        "valid": True,
        "translation": (tx, ty, tz),
        "rotation": (0, 0, 0),
        "message": f"相切约束: 平移 ({tx:.2f}, {ty:.2f}, {tz:.2f})",
    }


def solve_gear_mesh(src: Anchor, tgt: Anchor, module_val: float = 0) -> dict[str, Any]:
    """求解齿轮啮合约束。

    验证条件：
    1. 两齿轮轴线平行（同方向）
    2. 中心距 = (r1 + r2)（由 metadata 中的 pitch_radius 推算）
    3. 模数相同

    src: 主动齿轮的 gear_center 锚点
    tgt: 从动齿轮的 gear_center 锚点
    module_val: 模数值（0 表示从 metadata 推断）
    """
    # 检查轴线平行
    dot = (
        src.direction[0] * tgt.direction[0]
        + src.direction[1] * tgt.direction[1]
        + src.direction[2] * tgt.direction[2]
    )
    axes_parallel = abs(abs(dot) - 1.0) < 0.05

    # 从 metadata 获取节圆半径
    src_r = src.metadata.get("pitch_radius", 0) if isinstance(src.metadata, dict) else 0
    tgt_r = tgt.metadata.get("pitch_radius", 0) if isinstance(tgt.metadata, dict) else 0
    src_module = src.metadata.get("module", 0) if isinstance(src.metadata, dict) else 0
    tgt_module = tgt.metadata.get("module", 0) if isinstance(tgt.metadata, dict) else 0

    # 验证模数匹配
    module_ok = True
    if src_module > 0 and tgt_module > 0:
        module_ok = abs(src_module - tgt_module) < 0.01

    # 计算理想中心距
    ideal_cd = src_r + tgt_r
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]
    current_cd = math.sqrt(dx * dx + dy * dy + dz * dz)

    cd_ok = True
    if ideal_cd > 0:
        cd_ok = abs(current_cd - ideal_cd) < ideal_cd * 0.05  # 5% 容差

    valid = axes_parallel and module_ok and cd_ok

    issues = []
    if not axes_parallel:
        issues.append("轴线不平行")
    if not module_ok:
        issues.append(f"模数不匹配 ({src_module} vs {tgt_module})")
    if not cd_ok and ideal_cd > 0:
        issues.append(f"中心距偏差: 当前{current_cd:.2f}mm, 理想{ideal_cd:.2f}mm")

    # 计算平移修正
    tx, ty, tz = 0, 0, 0
    if ideal_cd > 0 and current_cd > 1e-6:
        factor = ideal_cd / current_cd
        tx = dx * factor - dx
        ty = dy * factor - dy
        tz = dz * factor - dz

    return {
        "valid": valid,
        "translation": (tx, ty, tz),
        "rotation": (0, 0, 0),
        "ideal_center_distance": ideal_cd,
        "current_center_distance": current_cd,
        "module_match": module_ok,
        "axes_parallel": axes_parallel,
        "message": "齿轮啮合: OK" if valid else f"齿轮啮合问题: {', '.join(issues)}",
    }


def solve_slider(src: Anchor, tgt: Anchor, max_travel: float = 0) -> dict[str, Any]:
    """求解滑动约束。

    约束源零件沿目标轴线方向滑动，限制其他自由度。

    src: 滑块/运动件的定位锚点
    tgt: 导轨/轴线的锚点（direction = 滑动方向）
    max_travel: 最大行程（0 = 不限）
    """
    # 对齐到轴线：将 src 投影到 tgt 定义的轴线上
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]

    # 沿轴线方向的投影
    axis = tgt.direction
    proj = dx * axis[0] + dy * axis[1] + dz * axis[2]

    # 位置修正：将 src 移动到轴线上（消除垂直于轴线的偏移）
    on_axis_x = tgt.position[0] + proj * axis[0]
    on_axis_y = tgt.position[1] + proj * axis[1]
    on_axis_z = tgt.position[2] + proj * axis[2]

    # 垂直偏移量
    perp_x = src.position[0] - on_axis_x
    perp_y = src.position[1] - on_axis_y
    perp_z = src.position[2] - on_axis_z
    perp_dist = math.sqrt(perp_x ** 2 + perp_y ** 2 + perp_z ** 2)

    # 需要消除垂直偏移
    tx = -perp_x
    ty = -perp_y
    tz = -perp_z

    within_travel = True
    if max_travel > 0:
        within_travel = abs(proj) <= max_travel / 2

    valid = perp_dist < 0.1 and within_travel

    return {
        "valid": valid,
        "translation": (tx, ty, tz),
        "rotation": (0, 0, 0),
        "slide_axis": axis,
        "slide_offset": proj,
        "perpendicular_error": perp_dist,
        "within_travel": within_travel,
        "message": f"滑动约束: 沿轴偏移 {proj:.2f}mm, 垂直偏差 {perp_dist:.2f}mm",
    }


def solve_rotational(src: Anchor, tgt: Anchor, angle_limit: float = 0) -> dict[str, Any]:
    """求解旋转约束。

    约束源零件绕目标轴线旋转，限制其他自由度。

    src: 旋转件的中心锚点
    tgt: 旋转轴线锚点（direction = 旋转轴方向）
    angle_limit: 角度限制（0 = 不限，>0 = 最大旋转角度）
    """
    # 检查轴线对齐：src 的方向应该与 tgt 的方向平行
    dot = (
        src.direction[0] * tgt.direction[0]
        + src.direction[1] * tgt.direction[1]
        + src.direction[2] * tgt.direction[2]
    )
    axes_aligned = abs(abs(dot) - 1.0) < 0.05

    # 位置修正：将 src 中心对齐到 tgt 轴线
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]

    # 沿旋转轴方向的偏移是允许的（旋转件可以沿轴移动）
    axis = tgt.direction
    proj = dx * axis[0] + dy * axis[1] + dz * axis[2]

    # 只消除垂直于旋转轴的偏移
    perp_x = dx - proj * axis[0]
    perp_y = dy - proj * axis[1]
    perp_z = dz - proj * axis[2]
    perp_dist = math.sqrt(perp_x ** 2 + perp_y ** 2 + perp_z ** 2)

    tx = perp_x
    ty = perp_y
    tz = perp_z

    valid = axes_aligned and perp_dist < 0.1

    return {
        "valid": valid,
        "translation": (tx, ty, tz),
        "rotation": (0, 0, 0),
        "rotation_axis": axis,
        "axes_aligned": axes_aligned,
        "center_error": perp_dist,
        "message": f"旋转约束: 轴线{'已对齐' if axes_aligned else '未对齐'}, 中心偏差 {perp_dist:.2f}mm",
    }


# 求解器路由表
SOLVERS = {
    "coincident": solve_coincident,
    "parallel": solve_parallel,
    "perpendicular": solve_perpendicular,
    "distance": solve_distance,
    "angle": solve_angle,
    "tangent": solve_tangent,
    "gear_mesh": solve_gear_mesh,
    "slider": solve_slider,
    "rotational": solve_rotational,
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

    if constraint.type in ("distance", "angle", "gear_mesh", "slider", "rotational"):
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
    "齿轮啮合": lambda parts: [
        Constraint(type="gear_mesh", source_anchor="gear_center", target_anchor="gear_center"),
    ],
    "滑动": lambda parts: [
        Constraint(type="slider", source_anchor="axis", target_anchor="axis"),
    ],
    "旋转": lambda parts: [
        Constraint(type="rotational", source_anchor="axis", target_anchor="axis"),
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
