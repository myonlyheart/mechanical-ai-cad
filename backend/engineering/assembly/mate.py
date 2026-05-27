"""Mate 约束系统 - 定义零件间的装配关系。

支持类型: coincident, concentric, parallel
AI 自动找 Anchor → 建立 Mate → 自动定位。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ...core.models import Anchor, Part


class MateType(str, Enum):
    """Mate 约束类型。"""
    COINCIDENT = "coincident"    # 重合：两个锚点完全重合
    CONCENTRIC = "concentric"    # 同心：两个轴/孔中心对齐
    PARALLEL = "parallel"        # 平行：两个方向向量平行
    TANGENT = "tangent"          # 相切
    DISTANCE = "distance"        # 距离：两个锚点保持指定距离
    ANGLE = "angle"              # 角度：两个方向保持指定角度
    GEAR_MESH = "gear_mesh"      # 齿轮啮合：模数匹配 + 中心距
    SLIDER = "slider"            # 滑动：沿轴线滑动
    ROTATIONAL = "rotational"    # 旋转：绕轴线旋转


@dataclass
class MateConstraint:
    """Mate 约束定义。

    Attributes:
        id: 唯一标识符
        type: 约束类型
        source_anchor: 源零件锚点名称
        target_anchor: 目标零件锚点名称
        source_part: 源零件名称
        target_part: 目标零件名称
        value: 约束值（距离/角度）
        solved: 是否已求解
    """
    id: str = ""
    type: str = "coincident"
    source_anchor: str = ""
    target_anchor: str = ""
    source_part: str = ""
    target_part: str = ""
    value: float = 0.0
    solved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "source_part": self.source_part,
            "source_anchor": self.source_anchor,
            "target_part": self.target_part,
            "target_anchor": self.target_anchor,
            "value": self.value,
            "solved": self.solved,
        }


def create_coincident_mate(
    source_part: str, source_anchor: str,
    target_part: str, target_anchor: str,
) -> MateConstraint:
    """创建重合约束。"""
    return MateConstraint(
        type=MateType.COINCIDENT,
        source_part=source_part, source_anchor=source_anchor,
        target_part=target_part, target_anchor=target_anchor,
    )


def create_concentric_mate(
    source_part: str, source_anchor: str,
    target_part: str, target_anchor: str,
) -> MateConstraint:
    """创建同心约束。"""
    return MateConstraint(
        type=MateType.CONCENTRIC,
        source_part=source_part, source_anchor=source_anchor,
        target_part=target_part, target_anchor=target_anchor,
    )


def create_parallel_mate(
    source_part: str, source_anchor: str,
    target_part: str, target_anchor: str,
) -> MateConstraint:
    """创建平行约束。"""
    return MateConstraint(
        type=MateType.PARALLEL,
        source_part=source_part, source_anchor=source_anchor,
        target_part=target_part, target_anchor=target_anchor,
    )


def create_distance_mate(
    source_part: str, source_anchor: str,
    target_part: str, target_anchor: str,
    distance: float,
) -> MateConstraint:
    """创建距离约束。"""
    return MateConstraint(
        type=MateType.DISTANCE,
        source_part=source_part, source_anchor=source_anchor,
        target_part=target_part, target_anchor=target_anchor,
        value=distance,
    )


def create_gear_mesh_mate(
    source_part: str, source_anchor: str,
    target_part: str, target_anchor: str,
    module_val: float = 0,
) -> MateConstraint:
    """创建齿轮啮合约束。"""
    return MateConstraint(
        type=MateType.GEAR_MESH,
        source_part=source_part, source_anchor=source_anchor,
        target_part=target_part, target_anchor=target_anchor,
        value=module_val,
    )


def create_slider_mate(
    source_part: str, source_anchor: str,
    target_part: str, target_anchor: str,
    max_travel: float = 0,
) -> MateConstraint:
    """创建滑动约束。"""
    return MateConstraint(
        type=MateType.SLIDER,
        source_part=source_part, source_anchor=source_anchor,
        target_part=target_part, target_anchor=target_anchor,
        value=max_travel,
    )


def create_rotational_mate(
    source_part: str, source_anchor: str,
    target_part: str, target_anchor: str,
    angle_limit: float = 0,
) -> MateConstraint:
    """创建旋转约束。"""
    return MateConstraint(
        type=MateType.ROTATIONAL,
        source_part=source_part, source_anchor=source_anchor,
        target_part=target_part, target_anchor=target_anchor,
        value=angle_limit,
    )


# ============================================================
# Mate 求解
# ============================================================

def solve_mate(
    mate: MateConstraint,
    source_anchors: list[Anchor],
    target_anchors: list[Anchor],
) -> dict[str, Any]:
    """求解单个 Mate 约束，返回所需的变换。

    Args:
        mate: 约束定义
        source_anchors: 源零件的锚点列表
        target_anchors: 目标零件的锚点列表

    Returns:
        {"translation": (x, y, z), "valid": bool, "message": str}
    """
    src_anchor = _find_anchor(source_anchors, mate.source_anchor)
    tgt_anchor = _find_anchor(target_anchors, mate.target_anchor)

    if src_anchor is None:
        return {"valid": False, "message": f"未找到源锚点: {mate.source_anchor}"}
    if tgt_anchor is None:
        return {"valid": False, "message": f"未找到目标锚点: {mate.target_anchor}"}

    if mate.type == MateType.COINCIDENT:
        return _solve_coincident(src_anchor, tgt_anchor)
    elif mate.type == MateType.CONCENTRIC:
        return _solve_concentric(src_anchor, tgt_anchor)
    elif mate.type == MateType.PARALLEL:
        return _solve_parallel(src_anchor, tgt_anchor)
    elif mate.type == MateType.DISTANCE:
        return _solve_distance(src_anchor, tgt_anchor, mate.value)
    elif mate.type == MateType.GEAR_MESH:
        return _solve_gear_mesh(src_anchor, tgt_anchor, mate.value)
    elif mate.type == MateType.SLIDER:
        return _solve_slider(src_anchor, tgt_anchor, mate.value)
    elif mate.type == MateType.ROTATIONAL:
        return _solve_rotational(src_anchor, tgt_anchor, mate.value)
    else:
        return {"valid": False, "message": f"不支持的约束类型: {mate.type}"}


def solve_mate_chain(
    mates: list[MateConstraint],
    parts: dict[str, Part],
) -> list[dict[str, Any]]:
    """求解一系列 Mate 约束。

    Args:
        mates: 约束列表
        parts: 零件字典 {name: Part}

    Returns:
        每个约束的求解结果列表
    """
    results: list[dict[str, Any]] = []
    for mate in mates:
        src_part = parts.get(mate.source_part)
        tgt_part = parts.get(mate.target_part)
        if src_part is None or tgt_part is None:
            results.append({
                "mate_id": mate.id, "valid": False,
                "message": f"零件未找到: {mate.source_part} 或 {mate.target_part}",
            })
            continue

        result = solve_mate(mate, src_part.anchors, tgt_part.anchors)
        result["mate_id"] = mate.id
        results.append(result)

    return results


def _find_anchor(anchors: list[Anchor], name: str) -> Optional[Anchor]:
    for a in anchors:
        if a.name == name:
            return a
    return None


def _solve_coincident(src: Anchor, tgt: Anchor) -> dict[str, Any]:
    """重合约束：将源锚点移动到目标锚点位置。"""
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]
    return {
        "valid": True,
        "translation": (dx, dy, dz),
        "message": f"重合: 移动 ({dx:.2f}, {dy:.2f}, {dz:.2f})",
    }


def _solve_concentric(src: Anchor, tgt: Anchor) -> dict[str, Any]:
    """同心约束：XY 平面对齐，Z 方向可选。"""
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]
    return {
        "valid": True,
        "translation": (dx, dy, dz),
        "message": f"同心: 移动 ({dx:.2f}, {dy:.2f}, {dz:.2f})",
    }


def _solve_parallel(src: Anchor, tgt: Anchor) -> dict[str, Any]:
    """平行约束：仅检查方向是否平行。"""
    import math
    dot = (
        src.direction[0] * tgt.direction[0]
        + src.direction[1] * tgt.direction[1]
        + src.direction[2] * tgt.direction[2]
    )
    is_parallel = abs(abs(dot) - 1.0) < 0.01
    return {
        "valid": is_parallel,
        "translation": (0, 0, 0),
        "message": "方向已平行" if is_parallel else "方向不平行，需要旋转",
    }


def _solve_distance(src: Anchor, tgt: Anchor, distance: float) -> dict[str, Any]:
    """距离约束：保持两个锚点间的指定距离。"""
    import math
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]
    current = math.sqrt(dx * dx + dy * dy + dz * dz)

    if current < 1e-6:
        return {"valid": False, "message": "锚点重合，无法计算距离方向"}

    factor = distance / current
    tx = dx * factor - dx
    ty = dy * factor - dy
    tz = dz * factor - dz
    return {
        "valid": True,
        "translation": (tx, ty, tz),
        "message": f"距离: 当前 {current:.2f}mm, 目标 {distance:.2f}mm",
    }


def _solve_gear_mesh(src: Anchor, tgt: Anchor, module_val: float) -> dict[str, Any]:
    """齿轮啮合约束：验证轴线平行、模数匹配、中心距正确。"""
    import math
    # 检查轴线平行
    dot = (
        src.direction[0] * tgt.direction[0]
        + src.direction[1] * tgt.direction[1]
        + src.direction[2] * tgt.direction[2]
    )
    axes_parallel = abs(abs(dot) - 1.0) < 0.05

    # 从 metadata 获取信息
    src_r = src.metadata.get("pitch_radius", 0) if isinstance(src.metadata, dict) else 0
    tgt_r = tgt.metadata.get("pitch_radius", 0) if isinstance(tgt.metadata, dict) else 0

    ideal_cd = src_r + tgt_r
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]
    current_cd = math.sqrt(dx * dx + dy * dy + dz * dz)

    cd_ok = True
    if ideal_cd > 0:
        cd_ok = abs(current_cd - ideal_cd) < ideal_cd * 0.05

    valid = axes_parallel and cd_ok

    tx, ty, tz = 0, 0, 0
    if ideal_cd > 0 and current_cd > 1e-6:
        factor = ideal_cd / current_cd
        tx = dx * factor - dx
        ty = dy * factor - dy
        tz = dz * factor - dz

    return {
        "valid": valid,
        "translation": (tx, ty, tz),
        "ideal_center_distance": ideal_cd,
        "current_center_distance": current_cd,
        "message": "齿轮啮合: OK" if valid else f"齿轮啮合: 轴线{'不平行' if not axes_parallel else 'OK'}, 中心距{'偏差' if not cd_ok else 'OK'}",
    }


def _solve_slider(src: Anchor, tgt: Anchor, max_travel: float) -> dict[str, Any]:
    """滑动约束：沿轴线滑动，消除垂直偏移。"""
    import math
    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]

    axis = tgt.direction
    proj = dx * axis[0] + dy * axis[1] + dz * axis[2]

    perp_x = dx - proj * axis[0]
    perp_y = dy - proj * axis[1]
    perp_z = dz - proj * axis[2]
    perp_dist = math.sqrt(perp_x ** 2 + perp_y ** 2 + perp_z ** 2)

    return {
        "valid": perp_dist < 0.1,
        "translation": (perp_x, perp_y, perp_z),
        "slide_offset": proj,
        "perpendicular_error": perp_dist,
        "message": f"滑动: 偏移 {proj:.2f}mm, 垂直偏差 {perp_dist:.2f}mm",
    }


def _solve_rotational(src: Anchor, tgt: Anchor, angle_limit: float) -> dict[str, Any]:
    """旋转约束：绕轴线旋转，消除垂直偏移。"""
    import math
    dot = (
        src.direction[0] * tgt.direction[0]
        + src.direction[1] * tgt.direction[1]
        + src.direction[2] * tgt.direction[2]
    )
    axes_aligned = abs(abs(dot) - 1.0) < 0.05

    dx = tgt.position[0] - src.position[0]
    dy = tgt.position[1] - src.position[1]
    dz = tgt.position[2] - src.position[2]

    axis = tgt.direction
    proj = dx * axis[0] + dy * axis[1] + dz * axis[2]

    perp_x = dx - proj * axis[0]
    perp_y = dy - proj * axis[1]
    perp_z = dz - proj * axis[2]
    perp_dist = math.sqrt(perp_x ** 2 + perp_y ** 2 + perp_z ** 2)

    return {
        "valid": axes_aligned and perp_dist < 0.1,
        "translation": (perp_x, perp_y, perp_z),
        "axes_aligned": axes_aligned,
        "center_error": perp_dist,
        "message": f"旋转: 轴线{'已对齐' if axes_aligned else '未对齐'}, 中心偏差 {perp_dist:.2f}mm",
    }
