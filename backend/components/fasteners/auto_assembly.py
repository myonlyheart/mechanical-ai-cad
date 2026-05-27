"""Auto fastener assembly - 自动紧固件装配。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ...core.models import Anchor
from .bolt_generator import Bolt, BoltParams
from .nut_generator import Nut, NutParams
from .washer_generator import Washer, WasherParams
from .hole_matcher import get_hole_diameter, recommend_bolt


@dataclass
class FastenerSet:
    """一组紧固件（螺栓+垫片+螺母）。"""
    bolt: dict[str, Any] = field(default_factory=dict)
    washer_top: dict[str, Any] = field(default_factory=dict)
    washer_bottom: dict[str, Any] = field(default_factory=dict)
    nut: dict[str, Any] = field(default_factory=dict)
    position: tuple[float, float, float] = (0, 0, 0)
    direction: tuple[float, float, float] = (0, 0, 1)
    total_length: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "bolt": self.bolt,
            "washer_top": self.washer_top,
            "washer_bottom": self.washer_bottom,
            "nut": self.nut,
            "position": self.position,
            "direction": self.direction,
            "total_length": round(self.total_length, 1),
        }


@dataclass
class AutoAssemblyResult:
    """自动装配结果。"""
    fastener_sets: list[FastenerSet] = field(default_factory=list)
    total_bolts: int = 0
    total_nuts: int = 0
    total_washers: int = 0
    bom_entries: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fastener_sets": [fs.to_dict() for fs in self.fastener_sets],
            "total_bolts": self.total_bolts,
            "total_nuts": self.total_nuts,
            "total_washers": self.total_washers,
            "bom_entries": self.bom_entries,
            "warnings": self.warnings,
        }


def _find_hole_anchors(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """从锚点列表中筛选出孔中心锚点。"""
    return [a for a in anchors if a.get("type") == "hole_center"]


def _compute_bolt_length(
    plate_thickness: float,
    nut_height: float,
    washer_thickness: float,
    extra_grip: float = 3.0,
) -> float:
    """计算所需螺栓长度。

    Args:
        plate_thickness: 板材总厚度
        nut_height: 螺母高度
        washer_thickness: 垫片厚度
        extra_grip: 额外余量

    Returns:
        推荐螺栓长度 (mm)
    """
    total = plate_thickness + nut_height + washer_thickness * 2 + extra_grip
    # 四舍五入到标准长度 (5, 10, 16, 20, 25, 30, 35, 40, 45, 50, ...)
    standard_lengths = [5, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100]
    for sl in standard_lengths:
        if sl >= total:
            return float(sl)
    return float(standard_lengths[-1])


def auto_fasten(
    anchors: list[dict[str, Any]],
    plate_thickness: float = 10.0,
    preferred_diameter: float = 0.0,
    strength_grade: str = "8.8",
    include_nut: bool = True,
    include_washer: bool = True,
) -> AutoAssemblyResult:
    """自动为装配体的孔位添加紧固件。

    Args:
        anchors: 孔锚点列表 [{"name": "...", "type": "hole_center", "diameter": 6.5, "position": [x,y,z], "direction": [dx,dy,dz]}, ...]
        plate_thickness: 板材总厚度
        preferred_diameter: 首选螺栓直径 (0=自动从孔径推算)
        strength_grade: 强度等级
        include_nut: 是否包含螺母
        include_washer: 是否包含垫片

    Returns:
        AutoAssemblyResult
    """
    result = AutoAssemblyResult()
    hole_anchors = _find_hole_anchors(anchors)

    if not hole_anchors:
        result.warnings.append("未找到孔锚点（hole_center 类型）")
        return result

    for hole in hole_anchors:
        hole_d = hole.get("diameter", 6.5)
        pos = hole.get("position", [0, 0, 0])
        direction = hole.get("direction", [0, 0, 1])
        hole_name = hole.get("name", "unknown")

        # 推荐螺栓
        if preferred_diameter > 0:
            bolt_d = preferred_diameter
        else:
            rec = recommend_bolt(hole_d)
            bolt_d = rec["diameter"]

        # 计算紧固件尺寸
        nut_h = bolt_d * 0.8 if bolt_d <= 10 else bolt_d * 0.85
        washer_t = 1.6 if bolt_d <= 8 else 2.0
        bolt_len = _compute_bolt_length(plate_thickness, nut_h, washer_t)

        # 创建紧固件组
        fs = FastenerSet(
            position=tuple(pos),
            direction=tuple(direction),
            total_length=bolt_len + (nut_h + washer_t * 2 if include_nut else 0),
            bolt={
                "part_type": "bolt",
                "diameter": bolt_d,
                "length": bolt_len,
                "head_type": "socket",
                "strength_grade": strength_grade,
                "name": f"M{int(bolt_d)}x{int(bolt_len)} bolt ({hole_name})",
            },
        )

        if include_washer:
            fs.washer_top = {
                "part_type": "washer",
                "inner_diameter": bolt_d + 0.4,
                "outer_diameter": bolt_d * 2,
                "thickness": washer_t,
                "name": f"M{int(bolt_d)} washer ({hole_name} top)",
            }
            fs.washer_bottom = {
                "part_type": "washer",
                "inner_diameter": bolt_d + 0.4,
                "outer_diameter": bolt_d * 2,
                "thickness": washer_t,
                "name": f"M{int(bolt_d)} washer ({hole_name} bottom)",
            }

        if include_nut:
            fs.nut = {
                "part_type": "nut",
                "diameter": bolt_d,
                "nut_type": "hex",
                "name": f"M{int(bolt_d)} nut ({hole_name})",
            }

        result.fastener_sets.append(fs)

    # 统计
    result.total_bolts = len(result.fastener_sets)
    result.total_nuts = len(result.fastener_sets) if include_nut else 0
    result.total_washers = len(result.fastener_sets) * 2 if include_washer else 0

    # BOM entries
    if result.total_bolts > 0:
        result.bom_entries.append({
            "part_type": "bolt",
            "name": f"M{int(result.fastener_sets[0].bolt['diameter'])}x{int(result.fastener_sets[0].bolt['length'])} 螺栓",
            "quantity": result.total_bolts,
        })
    if result.total_nuts > 0:
        result.bom_entries.append({
            "part_type": "nut",
            "name": f"M{int(result.fastener_sets[0].bolt['diameter'])} 螺母",
            "quantity": result.total_nuts,
        })
    if result.total_washers > 0:
        result.bom_entries.append({
            "part_type": "washer",
            "name": f"M{int(result.fastener_sets[0].bolt['diameter'])} 垫片",
            "quantity": result.total_washers,
        })

    return result
