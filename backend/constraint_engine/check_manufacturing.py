"""制造约束检查 - 3D 打印可行性校验"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ManufacturingIssue:
    """制造问题描述"""
    code: str
    message: str
    severity: str = "error"  # error | warning
    fix_suggestion: str = ""


# FDM 打印标准参数
FDM_MIN_WALL_THICKNESS = 1.2      # mm
FDM_MIN_HOLE_DIAMETER = 2.0       # mm
FDM_MAX_OVERHANG_ANGLE = 45       # 度
FDM_MIN_FEATURE_SIZE = 0.8        # mm
FDM_LAYER_HEIGHT_DEFAULT = 0.2    # mm
FDM_MIN_BRIDGE_LENGTH = 30        # mm


def check_wall_thickness(thickness: float, material: str = "PLA") -> list[ManufacturingIssue]:
    """检查壁厚是否满足最小要求"""
    issues = []
    min_thickness = FDM_MIN_WALL_THICKNESS

    if material.upper() in ("PLA", "PETG"):
        min_thickness = 1.2
    elif material.upper() == "ABS":
        min_thickness = 1.5
    elif material.upper() == "TPU":
        min_thickness = 1.0

    if thickness < min_thickness:
        issues.append(ManufacturingIssue(
            code="wall_too_thin",
            message=f"壁厚 {thickness}mm 低于 {material} 最小要求 {min_thickness}mm",
            severity="error",
            fix_suggestion=f"将壁厚增加到 {max(min_thickness, 2.0)}mm",
        ))
    elif thickness < min_thickness * 1.5:
        issues.append(ManufacturingIssue(
            code="wall_thin_warning",
            message=f"壁厚 {thickness}mm 接近最小值，建议增加到 {min_thickness * 1.5:.1f}mm",
            severity="warning",
        ))

    return issues


def check_hole_diameter(diameter: float) -> list[ManufacturingIssue]:
    """检查孔径是否满足打印精度"""
    issues = []

    if diameter < FDM_MIN_HOLE_DIAMETER:
        issues.append(ManufacturingIssue(
            code="hole_too_small",
            message=f"孔径 {diameter}mm 低于 FDM 最小可打印孔径 {FDM_MIN_HOLE_DIAMETER}mm",
            severity="error",
            fix_suggestion=f"将孔径增加到 {FDM_MIN_HOLE_DIAMETER + 0.5}mm 或使用打印后钻孔",
        ))

    return issues


def check_overhang_angle(angle: float) -> list[ManufacturingIssue]:
    """检查悬垂角是否在安全范围内"""
    issues = []

    if angle > FDM_MAX_OVERHANG_ANGLE:
        issues.append(ManufacturingIssue(
            code="overhang_too_large",
            message=f"悬垂角 {angle}° 超过 FDM 安全角度 {FDM_MAX_OVERHANG_ANGLE}°",
            severity="error",
            fix_suggestion=f"将悬垂角减小到 {FDM_MAX_OVERHANG_ANGLE}° 以下或添加支撑结构",
        ))

    return issues


def check_geometry_closed(is_closed: bool) -> list[ManufacturingIssue]:
    """检查是否为封闭体（水密）"""
    issues = []

    if not is_closed:
        issues.append(ManufacturingIssue(
            code="not_closed_solid",
            message="模型不是封闭体，无法用于 3D 打印",
            severity="error",
            fix_suggestion="修复所有开放边或面，确保模型为水密实体",
        ))

    return issues


def check_min_feature_size(size: float) -> list[ManufacturingIssue]:
    """检查最小特征尺寸"""
    issues = []

    if size < FDM_MIN_FEATURE_SIZE:
        issues.append(ManufacturingIssue(
            code="feature_too_small",
            message=f"特征尺寸 {size}mm 低于 FDM 最小可打印尺寸 {FDM_MIN_FEATURE_SIZE}mm",
            severity="warning",
            fix_suggestion=f"将特征尺寸增加到 {FDM_MIN_FEATURE_SIZE}mm 以上",
        ))

    return issues


def check_manufacturability(params: dict) -> dict:
    """综合制造可行性检查"""
    all_issues: list[dict] = []

    thickness = params.get("thickness", params.get("base_thickness", 5))
    material = params.get("material", "PLA")
    hole_diameter = params.get("hole_diameter", params.get("mounting_hole_diameter", 5))

    # 壁厚检查
    for issue in check_wall_thickness(thickness, material):
        all_issues.append({"code": issue.code, "message": issue.message, "severity": issue.severity, "fix": issue.fix_suggestion})

    # 孔径检查
    if hole_diameter:
        for issue in check_hole_diameter(hole_diameter):
            all_issues.append({"code": issue.code, "message": issue.message, "severity": issue.severity, "fix": issue.fix_suggestion})

    has_error = any(i["severity"] == "error" for i in all_issues)

    return {
        "valid": not has_error,
        "issues": all_issues,
        "checks_performed": ["wall_thickness", "hole_diameter"],
    }
