"""Repair Engine - 基于工程规则的自动修复引擎。

核心原则：
- 禁止随机修改模型
- 必须基于工程规则修复
- 每次修复给出问题描述 + 解决方案 + 参数调整
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..validation.geometry import GeometryValidationResult, ValidationError
from ..validation.manufacturing import ManufacturingIssue, ManufacturingProcess
from ..validation.collision import CollisionResult


# ============================================================
# 修复建议数据结构
# ============================================================

@dataclass
class RepairSuggestion:
    """修复建议。"""
    id: str = ""
    problem: str = ""
    solution: str = ""
    severity: str = "error"
    auto_fixable: bool = False
    params_change: dict[str, Any] = field(default_factory=dict)
    rule: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "problem": self.problem,
            "solution": self.solution,
            "severity": self.severity,
            "auto_fixable": self.auto_fixable,
            "params_change": self.params_change,
            "rule": self.rule,
        }


@dataclass
class RepairResult:
    """修复结果。"""
    original_params: dict[str, Any] = field(default_factory=dict)
    repaired_params: dict[str, Any] = field(default_factory=dict)
    suggestions: list[RepairSuggestion] = field(default_factory=list)
    applied_fixes: list[str] = field(default_factory=list)
    remaining_issues: list[dict[str, Any]] = field(default_factory=list)
    fully_repaired: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_params": self.original_params,
            "repaired_params": self.repaired_params,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "applied_fixes": self.applied_fixes,
            "remaining_issues": self.remaining_issues,
            "fully_repaired": self.fully_repaired,
        }


# ============================================================
# 修复规则引擎
# ============================================================

@dataclass
class RepairRule:
    """修复规则定义。"""
    issue_code: str
    description: str
    check: Callable[[dict[str, Any]], bool]
    fix: Callable[[dict[str, Any]], tuple[dict[str, Any], str]]


def _fix_wall_too_thin(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """壁厚不足 → 增加壁厚到安全值。"""
    new_params = dict(params)
    min_safe = max(1.2 * 1.5, 2.0)
    for key in ("thickness", "base_thickness", "wall_thickness"):
        if key in new_params and new_params[key] < min_safe:
            old = new_params[key]
            new_params[key] = round(min_safe, 1)
            return new_params, f"{key}: {old}mm → {new_params[key]}mm"
    new_params["thickness"] = round(min_safe, 1)
    return new_params, f"thickness 设置为 {min_safe:.1f}mm"


def _fix_hole_too_small(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """孔径过小 → 增大到最小可打印值。"""
    new_params = dict(params)
    target = 2.5
    for key in ("hole_diameter", "mounting_hole_diameter"):
        if key in new_params and new_params[key] < target:
            old = new_params[key]
            new_params[key] = round(target, 1)
            return new_params, f"{key}: {old}mm → {new_params[key]}mm"
    return new_params, ""


def _fix_feature_too_small(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """特征尺寸过小 → 增大到最小可打印尺寸。"""
    new_params = dict(params)
    if "min_feature" in new_params and new_params["min_feature"] < 0.8:
        new_params["min_feature"] = 0.8
        return new_params, "min_feature: 调整为 0.8mm"
    return new_params, ""


def _fix_overhang_too_large(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """悬垂角过大 → 建议减小或添加支撑。"""
    new_params = dict(params)
    if "overhang_angle" in new_params and new_params["overhang_angle"] > 45:
        new_params["overhang_angle"] = 45
        new_params["add_support"] = True
        return new_params, "overhang_angle: 限制为 45°，启用支撑"
    return new_params, ""


def _fix_not_closed(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """非封闭体 → 标记需修复几何。"""
    new_params = dict(params)
    new_params["_needs_geometry_fix"] = True
    return new_params, "几何体需封闭修复（请检查开放边）"


def _fix_self_intersection(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """自相交 → 标记需修复几何。"""
    new_params = dict(params)
    new_params["_needs_geometry_fix"] = True
    return new_params, "几何体存在自相交（请检查拉伸/布尔运算参数）"


def _fix_zero_thickness(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """零厚度 → 增加最小厚度。"""
    new_params = dict(params)
    for key in ("thickness", "base_thickness"):
        if key in new_params and new_params[key] < 0.5:
            new_params[key] = 0.5
            return new_params, f"{key}: 调整为 0.5mm（最小安全厚度）"
    return new_params, ""


def _fix_collision(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """零件碰撞 → 标记需调整位置。"""
    new_params = dict(params)
    new_params["_needs_position_adjust"] = True
    return new_params, "零件存在碰撞（请调整装配位置）"


def _fix_nema_hole_spacing(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """NEMA 孔间距不标准 → 按标准修复。"""
    from ...constraint_engine.check_standard_parts import NEMA_STANDARDS
    new_params = dict(params)
    motor = params.get("motor_type", "")
    if motor in NEMA_STANDARDS:
        target = NEMA_STANDARDS[motor]["mounting_hole_spacing"]
        new_params["motor_hole_spacing"] = target
        return new_params, f"motor_hole_spacing: 调整为 {target}mm（{motor} 标准）"
    return new_params, ""


def _fix_nema_hole_diameter(params: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """NEMA 孔径不标准 → 按标准修复。"""
    from ...constraint_engine.check_standard_parts import NEMA_STANDARDS
    new_params = dict(params)
    motor = params.get("motor_type", "")
    if motor in NEMA_STANDARDS:
        target = NEMA_STANDARDS[motor]["mounting_hole_diameter"] + 0.3
        new_params["mounting_hole_diameter"] = round(target, 1)
        return new_params, f"mounting_hole_diameter: 调整为 {new_params['mounting_hole_diameter']}mm（{motor} 标准）"
    return new_params, ""


# 修复规则注册表
REPAIR_RULES: dict[str, RepairRule] = {
    "wall_too_thin": RepairRule("wall_too_thin", "壁厚不足", lambda p: True, _fix_wall_too_thin),
    "hole_too_small": RepairRule("hole_too_small", "孔径过小", lambda p: True, _fix_hole_too_small),
    "feature_too_small": RepairRule("feature_too_small", "特征尺寸过小", lambda p: True, _fix_feature_too_small),
    "overhang_too_large": RepairRule("overhang_too_large", "悬垂角过大", lambda p: True, _fix_overhang_too_large),
    "not_closed": RepairRule("not_closed", "非封闭体", lambda p: True, _fix_not_closed),
    "invalid_geometry": RepairRule("invalid_geometry", "几何无效", lambda p: True, _fix_self_intersection),
    "zero_thickness": RepairRule("zero_thickness", "零厚度", lambda p: True, _fix_zero_thickness),
    "collision": RepairRule("collision", "零件碰撞", lambda p: True, _fix_collision),
    "nema_hole_spacing_wrong": RepairRule("nema_hole_spacing_wrong", "NEMA孔间距不标准", lambda p: True, _fix_nema_hole_spacing),
    "nema_hole_too_small": RepairRule("nema_hole_too_small", "NEMA孔径不标准", lambda p: True, _fix_nema_hole_diameter),
}


# ============================================================
# 修复引擎主入口
# ============================================================

def generate_suggestions(
    params: dict[str, Any],
    issues: list[dict[str, Any]],
) -> list[RepairSuggestion]:
    """根据问题列表生成修复建议。"""
    suggestions: list[RepairSuggestion] = []

    for issue in issues:
        code = issue.get("code", "")
        message = issue.get("message", "")
        severity = issue.get("severity", "error")

        rule = REPAIR_RULES.get(code)
        if rule:
            suggestions.append(RepairSuggestion(
                problem=message,
                solution=rule.description,
                severity=severity,
                auto_fixable=True,
                rule=code,
            ))
        else:
            suggestions.append(RepairSuggestion(
                problem=message,
                solution="请手动检查并修复",
                severity=severity,
                auto_fixable=False,
            ))

    return suggestions


def auto_repair(
    params: dict[str, Any],
    issues: list[dict[str, Any]],
) -> RepairResult:
    """自动修复参数。

    Args:
        params: 原始参数
        issues: 问题列表 [{"code": "wall_too_thin", "message": "...", "severity": "error"}, ...]

    Returns:
        RepairResult
    """
    current_params = dict(params)
    applied: list[str] = []
    suggestions = generate_suggestions(params, issues)

    # 仅修复 error 级别且可自动修复的问题
    error_issues = [i for i in issues if i.get("severity") == "error"]

    for issue in error_issues:
        code = issue.get("code", "")
        rule = REPAIR_RULES.get(code)
        if rule:
            current_params, fix_msg = rule.fix(current_params)
            if fix_msg:
                applied.append(f"[{code}] {fix_msg}")

    # 标记无法自动修复的 remaining issues
    remaining = []
    for issue in error_issues:
        code = issue.get("code", "")
        if code in REPAIR_RULES and any(f"[{code}]" in f for f in applied):
            continue
        remaining.append(issue)

    return RepairResult(
        original_params=params,
        repaired_params=current_params,
        suggestions=suggestions,
        applied_fixes=applied,
        remaining_issues=remaining,
        fully_repaired=len(remaining) == 0,
    )


def full_repair_pipeline(
    params: dict[str, Any],
    geometry: Any = None,
    part_type: str = "",
) -> RepairResult:
    """完整修复流水线：校验 → 建议 → 修复 → 重校验。

    Args:
        params: 零件参数
        geometry: build123d 几何对象（可选）
        part_type: 零件类型

    Returns:
        RepairResult
    """
    from ..validation.geometry import validate_geometry
    from ..validation.manufacturing import validate_manufacturing

    all_issues: list[dict[str, Any]] = []

    # 几何校验
    if geometry is not None:
        geo_result = validate_geometry(geometry)
        for err in geo_result.errors:
            all_issues.append(err.to_dict())
        for warn in geo_result.warnings:
            all_issues.append(warn.to_dict())

    # 制造校验
    mfg_result = validate_manufacturing(params)
    all_issues.extend(mfg_result.get("issues", []))

    # 执行修复
    result = auto_repair(params, all_issues)

    # 修复后重校验
    if result.applied_fixes:
        post_mfg = validate_manufacturing(result.repaired_params)
        result.remaining_issues.extend(post_mfg.get("issues", []))
        result.fully_repaired = (
            len([i for i in result.remaining_issues if i.get("severity") == "error"]) == 0
        )

    return result
