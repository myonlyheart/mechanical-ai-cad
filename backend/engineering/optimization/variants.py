"""多方案生成 + 评分系统。

支持目标：轻量化、高强度、少材料、易打印、易加工
综合评分 = manufacturability + printability + strength + cost + weight
扩展现有 design_generator/design_variants.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ...constraint_engine import check_and_fix
from ..validation.manufacturing import validate_manufacturing, ManufacturingProcess


# ============================================================
# 评分权重配置
# ============================================================

@dataclass
class ScoringWeights:
    """评分权重。"""
    manufacturability: float = 0.25
    printability: float = 0.25
    strength: float = 0.20
    cost: float = 0.15
    weight: float = 0.15

    @classmethod
    def lightweight(cls) -> ScoringWeights:
        return cls(manufacturability=0.2, printability=0.2, strength=0.1, cost=0.1, weight=0.4)

    @classmethod
    def high_strength(cls) -> ScoringWeights:
        return cls(manufacturability=0.15, printability=0.15, strength=0.45, cost=0.1, weight=0.15)

    @classmethod
    def low_cost(cls) -> ScoringWeights:
        return cls(manufacturability=0.2, printability=0.2, strength=0.15, cost=0.35, weight=0.1)

    @classmethod
    def easy_print(cls) -> ScoringWeights:
        return cls(manufacturability=0.15, printability=0.45, strength=0.15, cost=0.1, weight=0.15)


# ============================================================
# 单项评分函数
# ============================================================

def score_manufacturability(params: dict[str, Any]) -> float:
    """可制造性评分 (0-100)。"""
    score = 100.0
    thickness = params.get("thickness", params.get("base_thickness", 5))
    hole_dia = params.get("hole_diameter", params.get("mounting_hole_diameter", 5))

    # 壁厚扣分
    if thickness < 1.2:
        score -= 40
    elif thickness < 1.8:
        score -= 20

    # 孔径扣分
    if hole_dia and hole_dia < 2.0:
        score -= 30
    elif hole_dia and hole_dia < 3.0:
        score -= 10

    return max(0, score)


def score_printability(params: dict[str, Any]) -> float:
    """3D 打印友好性评分 (0-100)。"""
    score = 100.0
    thickness = params.get("thickness", params.get("base_thickness", 5))
    overhang = params.get("overhang_angle", 0)

    # 悬垂角扣分
    if overhang > 45:
        score -= 50
    elif overhang > 30:
        score -= 20

    # 壁厚过厚扣分（打印时间）
    if thickness > 8:
        score -= 15

    # 添加支撑扣分
    if params.get("add_support"):
        score -= 15

    return max(0, score)


def score_strength(params: dict[str, Any]) -> float:
    """强度评分 (0-100)。"""
    score = 50.0
    thickness = params.get("thickness", params.get("base_thickness", 5))

    # 厚度加分
    score += min(thickness * 5, 30)

    # 加强筋加分
    if params.get("add_ribs"):
        score += 15
    if params.get("add_gussets"):
        score += 10

    # 晶格/中空扣分
    if params.get("lattice_fill"):
        score -= 20
    if params.get("hollow"):
        score -= 15

    return max(0, min(100, score))


def score_cost(params: dict[str, Any]) -> float:
    """成本评分 (0-100, 越高越便宜)。"""
    score = 80.0
    thickness = params.get("thickness", params.get("base_thickness", 5))
    material = params.get("material", "PLA")

    # 材料成本
    material_cost = {"PLA": 0, "PETG": 5, "ABS": 10, "TPU": 20, "Nylon": 25}
    score -= material_cost.get(material, 0)

    # 厚度影响材料用量
    if thickness > 6:
        score -= (thickness - 6) * 3

    # 额外特征增加成本
    if params.get("lattice_fill"):
        score -= 10
    if params.get("adjustable_height"):
        score -= 5

    return max(0, min(100, score))


def score_weight(params: dict[str, Any]) -> float:
    """轻量化评分 (0-100, 越高越轻)。"""
    score = 70.0
    thickness = params.get("thickness", params.get("base_thickness", 5))

    # 薄壁加分
    if thickness < 2:
        score += 20
    elif thickness < 3:
        score += 10
    elif thickness > 6:
        score -= (thickness - 6) * 5

    # 减重特征加分
    if params.get("hollow"):
        score += 15
    if params.get("lattice_fill"):
        score += 20
    if params.get("web_style") == "spoked":
        score += 10

    return max(0, min(100, score))


# ============================================================
# 综合评分
# ============================================================

SCORE_FUNCTIONS: dict[str, Callable[[dict[str, Any]], float]] = {
    "manufacturability": score_manufacturability,
    "printability": score_printability,
    "strength": score_strength,
    "cost": score_cost,
    "weight": score_weight,
}


def score_variant(
    params: dict[str, Any],
    weights: ScoringWeights | None = None,
) -> dict[str, Any]:
    """综合评分一个变体。

    Args:
        params: 零件参数
        weights: 评分权重（默认均衡）

    Returns:
        {"total": float, "breakdown": {...}, "grade": str}
    """
    if weights is None:
        weights = ScoringWeights()

    breakdown: dict[str, float] = {}
    for name, func in SCORE_FUNCTIONS.items():
        breakdown[name] = round(func(params), 1)

    total = round(
        breakdown["manufacturability"] * weights.manufacturability
        + breakdown["printability"] * weights.printability
        + breakdown["strength"] * weights.strength
        + breakdown["cost"] * weights.cost
        + breakdown["weight"] * weights.weight,
        1,
    )

    # 等级
    if total >= 85:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 55:
        grade = "C"
    elif total >= 40:
        grade = "D"
    else:
        grade = "F"

    return {
        "total": total,
        "breakdown": breakdown,
        "grade": grade,
        "weights": {
            "manufacturability": weights.manufacturability,
            "printability": weights.printability,
            "strength": weights.strength,
            "cost": weights.cost,
            "weight": weights.weight,
        },
    }


# ============================================================
# 多方案生成主入口
# ============================================================

def generate_variants(
    part_type: str,
    base_params: dict[str, Any],
    designs: list[dict[str, Any]],
    optimization_goal: str = "balanced",
) -> list[dict[str, Any]]:
    """生成多个参数变体并评分。

    Args:
        part_type: 零件类型
        base_params: 基础参数
        designs: 设计方案列表
        optimization_goal: 优化目标 (balanced | lightweight | high_strength | low_cost | easy_print)

    Returns:
        变体列表（含评分和约束检查结果）
    """
    # 选择评分权重
    weight_map: dict[str, ScoringWeights] = {
        "balanced": ScoringWeights(),
        "lightweight": ScoringWeights.lightweight(),
        "high_strength": ScoringWeights.high_strength(),
        "low_cost": ScoringWeights.low_cost(),
        "easy_print": ScoringWeights.easy_print(),
    }
    weights = weight_map.get(optimization_goal, ScoringWeights())

    variants: list[dict[str, Any]] = []

    for design in designs:
        # 合并参数
        params = dict(base_params)
        params.update(design.get("params_override", {}))

        # 约束检查 + 自动修复
        check_result = check_and_fix(part_type, params)
        fixed_params = check_result["fixed_params"]

        # 评分
        scores = score_variant(fixed_params, weights)

        variant = {
            "design_id": design.get("design_id", ""),
            "name": design.get("name", ""),
            "description": design.get("description", ""),
            "params": fixed_params,
            "constraint_check": {
                "valid": check_result["valid"],
                "fixes_applied": check_result["fixes_applied"],
                "remaining_issues": check_result.get("remaining_issues", []),
            },
            "performance": {
                "weight": design.get("estimated_weight", ""),
                "strength": design.get("estimated_strength", ""),
                "print_time": design.get("estimated_print_time", ""),
            },
            "scores": scores,
        }
        variants.append(variant)

    # 按总分排序（高分在前）
    variants.sort(key=lambda v: v["scores"]["total"], reverse=True)

    return variants


def compare_variants(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """生成变体对比表。"""
    comparison: list[dict[str, Any]] = []
    for v in variants:
        comparison.append({
            "design_id": v["design_id"],
            "name": v["name"],
            "total_score": v["scores"]["total"],
            "grade": v["scores"]["grade"],
            "manufacturability": v["scores"]["breakdown"]["manufacturability"],
            "printability": v["scores"]["breakdown"]["printability"],
            "strength": v["scores"]["breakdown"]["strength"],
            "cost": v["scores"]["breakdown"]["cost"],
            "weight": v["scores"]["breakdown"]["weight"],
            "valid": v["constraint_check"]["valid"],
        })
    return comparison


def recommend_variant(variants: list[dict[str, Any]]) -> str:
    """推荐最优变体 ID。"""
    if not variants:
        return ""
    return variants[0]["design_id"]
