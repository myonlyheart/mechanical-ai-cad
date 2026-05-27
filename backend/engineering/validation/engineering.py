"""工程语义校验 - 检查零件间的工程兼容性。

检查项：
- 齿轮模数匹配
- 轴-轴承配合
- 齿轮中心距
- 螺栓-孔匹配
- 轴-齿轮配合
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EngineeringIssue:
    """工程校验问题。"""
    code: str
    message: str
    severity: str = "warning"  # error | warning | info
    fix_suggestion: str = ""
    parts_involved: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "fix_suggestion": self.fix_suggestion,
            "parts_involved": self.parts_involved,
        }


@dataclass
class EngineeringValidationResult:
    """工程校验结果。"""
    valid: bool = True
    issues: list[EngineeringIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": [i.to_dict() for i in self.issues],
            "error_count": sum(1 for i in self.issues if i.severity == "error"),
            "warning_count": sum(1 for i in self.issues if i.severity == "warning"),
        }


# ============================================================
# 齿轮校验
# ============================================================

def check_gear_module_match(gear_a: dict, gear_b: dict) -> EngineeringIssue | None:
    """检查两个齿轮的模数是否匹配。"""
    mod_a = gear_a.get("module", 0)
    mod_b = gear_b.get("module", 0)
    name_a = gear_a.get("name", "gear_a")
    name_b = gear_b.get("name", "gear_b")

    if mod_a > 0 and mod_b > 0 and abs(mod_a - mod_b) > 0.01:
        return EngineeringIssue(
            code="gear_module_mismatch",
            message=f"齿轮模数不匹配: {name_a}(m={mod_a}) vs {name_b}(m={mod_b})",
            severity="error",
            fix_suggestion=f"将两齿轮模数统一为 {mod_a} 或 {mod_b}",
            parts_involved=[name_a, name_b],
        )
    return None


def check_gear_center_distance(gear_a: dict, gear_b: dict) -> EngineeringIssue | None:
    """检查齿轮中心距是否正确。"""
    mod_a = gear_a.get("module", 0)
    mod_b = gear_b.get("module", 0)
    teeth_a = gear_a.get("tooth_count", 0)
    teeth_b = gear_b.get("tooth_count", 0)
    pos_a = gear_a.get("position", (0, 0, 0))
    pos_b = gear_b.get("position", (0, 0, 0))
    name_a = gear_a.get("name", "gear_a")
    name_b = gear_b.get("name", "gear_b")

    if mod_a <= 0 or teeth_a <= 0 or teeth_b <= 0:
        return None

    ideal_cd = (mod_a * teeth_a + mod_b * teeth_b) / 2
    dx = pos_b[0] - pos_a[0]
    dy = pos_b[1] - pos_a[1]
    dz = pos_b[2] - pos_a[2]
    actual_cd = math.sqrt(dx * dx + dy * dy + dz * dz)

    if actual_cd > 0 and abs(actual_cd - ideal_cd) > ideal_cd * 0.05:
        return EngineeringIssue(
            code="gear_center_distance_error",
            message=f"齿轮中心距偏差: 实际{actual_cd:.2f}mm, 理想{ideal_cd:.2f}mm",
            severity="warning",
            fix_suggestion=f"调整齿轮位置使中心距为 {ideal_cd:.1f}mm",
            parts_involved=[name_a, name_b],
        )
    return None


def check_gear_min_teeth(gear: dict) -> EngineeringIssue | None:
    """检查齿轮最小齿数（避免根切）。"""
    teeth = gear.get("tooth_count", 0)
    name = gear.get("name", "gear")

    if 0 < teeth < 12:
        return EngineeringIssue(
            code="gear_too_few_teeth",
            message=f"齿轮齿数过少: {teeth}齿（最少12齿避免根切）",
            severity="warning",
            fix_suggestion="增加齿数到12以上，或使用变位齿轮",
            parts_involved=[name],
        )
    return None


# ============================================================
# 轴-轴承配合校验
# ============================================================

def check_shaft_bearing_fit(shaft: dict, bearing: dict) -> EngineeringIssue | None:
    """检查轴与轴承的配合尺寸。"""
    shaft_d = shaft.get("diameter", 0)
    bearing_id = bearing.get("inner_diameter", 0)
    name_shaft = shaft.get("name", "shaft")
    name_bearing = bearing.get("name", "bearing")

    if shaft_d <= 0 or bearing_id <= 0:
        return None

    if abs(shaft_d - bearing_id) > 0.1:
        return EngineeringIssue(
            code="shaft_bearing_fit_error",
            message=f"轴-轴承配合错误: 轴径{shaft_d}mm vs 轴承内径{bearing_id}mm",
            severity="error",
            fix_suggestion=f"选择内径为{shaft_d}mm的轴承，或使用直径为{bearing_id}mm的轴",
            parts_involved=[name_shaft, name_bearing],
        )
    return None


def check_bearing_housing_fit(bearing: dict, housing: dict) -> EngineeringIssue | None:
    """检查轴承与轴承座的配合尺寸。"""
    bearing_od = bearing.get("outer_diameter", 0)
    housing_bore = housing.get("bearing_diameter", housing.get("bore_diameter", 0))
    name_bearing = bearing.get("name", "bearing")
    name_housing = housing.get("name", "housing")

    if bearing_od <= 0 or housing_bore <= 0:
        return None

    diff = housing_bore - bearing_od
    if diff < -0.1 or diff > 1.0:
        return EngineeringIssue(
            code="bearing_housing_fit_error",
            message=f"轴承-座配合错误: 轴承外径{bearing_od}mm vs 座孔{housing_bore}mm",
            severity="error",
            fix_suggestion=f"轴承座孔应为{bearing_od + 0.2:.1f}mm（配合间隙0.2mm）",
            parts_involved=[name_bearing, name_housing],
        )
    return None


# ============================================================
# 螺栓-孔匹配校验
# ============================================================

def check_bolt_hole_fit(bolt: dict, hole_diameter: float) -> EngineeringIssue | None:
    """检查螺栓与孔的配合。"""
    bolt_d = bolt.get("diameter", 0)
    name = bolt.get("name", "bolt")

    if bolt_d <= 0 or hole_diameter <= 0:
        return None

    clearance = hole_diameter - bolt_d
    if clearance < 0.3:
        return EngineeringIssue(
            code="bolt_hole_too_tight",
            message=f"螺栓孔过紧: M{bolt_d}螺栓 vs {hole_diameter}mm孔（间隙仅{clearance:.1f}mm）",
            severity="warning",
            fix_suggestion=f"将孔径增大到{bolt_d + 0.5:.1f}mm（标准间隙0.5mm）",
            parts_involved=[name],
        )
    elif clearance > 3.0:
        return EngineeringIssue(
            code="bolt_hole_too_loose",
            message=f"螺栓孔过大: M{bolt_d}螺栓 vs {hole_diameter}mm孔（间隙{clearance:.1f}mm）",
            severity="warning",
            fix_suggestion=f"将孔径减小到{bolt_d + 1.0:.1f}mm",
            parts_involved=[name],
        )
    return None


# ============================================================
# 通用装配校验
# ============================================================

def validate_assembly(parts: list[dict]) -> EngineeringValidationResult:
    """校验装配体中所有零件的工程兼容性。

    Args:
        parts: 零件列表 [{"name": "g1", "part_type": "gear", "params": {...}}, ...]

    Returns:
        EngineeringValidationResult
    """
    result = EngineeringValidationResult()

    # 按类型分组
    gears = []
    shafts = []
    bearings = []
    housings = []
    bolts = []

    for p in parts:
        ptype = p.get("part_type", "")
        params = p.get("params", {})
        entry = {"name": p.get("name", ""), **params, "position": p.get("position", (0, 0, 0))}

        if ptype == "gear":
            gears.append(entry)
        elif ptype == "shaft":
            shafts.append(entry)
        elif ptype == "bearing":
            bearings.append(entry)
        elif ptype in ("bearing_block",):
            housings.append(entry)
        elif ptype == "bolt":
            bolts.append(entry)

    # 齿轮互检
    for i in range(len(gears)):
        for j in range(i + 1, len(gears)):
            issue = check_gear_module_match(gears[i], gears[j])
            if issue:
                result.issues.append(issue)
            issue = check_gear_center_distance(gears[i], gears[j])
            if issue:
                result.issues.append(issue)
        issue = check_gear_min_teeth(gears[i])
        if issue:
            result.issues.append(issue)

    # 轴-轴承配合
    for shaft in shafts:
        for bearing in bearings:
            issue = check_shaft_bearing_fit(shaft, bearing)
            if issue:
                result.issues.append(issue)

    # 轴承-座配合
    for bearing in bearings:
        for housing in housings:
            issue = check_bearing_housing_fit(bearing, housing)
            if issue:
                result.issues.append(issue)

    # 标记是否有 error
    result.valid = not any(i.severity == "error" for i in result.issues)

    return result
