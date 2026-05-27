"""制造校验 - 检查零件的可制造性。

支持制造方式：CNC, 3D打印, 注塑（预留）
扩展现有 backend/constraint_engine/check_manufacturing.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ManufacturingProcess(str, Enum):
    """制造工艺类型。"""
    FDM_3D_PRINT = "fdm_3d_print"
    CNC_MILLING = "cnc_milling"
    INJECTION_MOLDING = "injection_molding"


@dataclass
class ManufacturingIssue:
    """制造问题描述。"""
    code: str = ""
    message: str = ""
    severity: str = "error"  # error | warning
    fix_suggestion: str = ""
    process: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code, "message": self.message,
            "severity": self.severity, "fix_suggestion": self.fix_suggestion,
            "process": self.process,
        }


# ============================================================
# FDM 3D 打印标准参数
# ============================================================

FDM_MIN_WALL_THICKNESS = 1.2      # mm
FDM_MIN_HOLE_DIAMETER = 2.0       # mm
FDM_MAX_OVERHANG_ANGLE = 45       # 度
FDM_MIN_FEATURE_SIZE = 0.8        # mm
FDM_LAYER_HEIGHT_DEFAULT = 0.2    # mm
FDM_MIN_BRIDGE_LENGTH = 30        # mm
FDM_MAX_SUPPORTED_ANGLE = 80      # 度（需要支撑）


# ============================================================
# CNC 铣削标准参数
# ============================================================

CNC_MIN_WALL_THICKNESS = 0.5      # mm
CNC_MIN_HOLE_DIAMETER = 1.0       # mm
CNC_MIN_FILLET_RADIUS = 0.3       # mm
CNC_MAX_ASPECT_RATIO = 10.0       # 深宽比


# ============================================================
# 注塑标准参数（预留）
# ============================================================

INJ_MIN_WALL_THICKNESS = 0.8      # mm
INJ_MAX_WALL_THICKNESS = 4.0      # mm
INJ_MIN_DRAFT_ANGLE = 1.0         # 度


# ============================================================
# 校验函数
# ============================================================

def check_wall_thickness(
    thickness: float, material: str = "PLA",
    process: str = ManufacturingProcess.FDM_3D_PRINT,
) -> list[ManufacturingIssue]:
    """检查壁厚。"""
    issues: list[ManufacturingIssue] = []

    if process == ManufacturingProcess.FDM_3D_PRINT:
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
                process=process,
            ))
        elif thickness < min_thickness * 1.5:
            issues.append(ManufacturingIssue(
                code="wall_thin_warning",
                message=f"壁厚 {thickness}mm 接近最小值，建议增加到 {min_thickness * 1.5:.1f}mm",
                severity="warning",
                process=process,
            ))

    elif process == ManufacturingProcess.CNC_MILLING:
        if thickness < CNC_MIN_WALL_THICKNESS:
            issues.append(ManufacturingIssue(
                code="wall_too_thin",
                message=f"壁厚 {thickness}mm 低于 CNC 最小要求 {CNC_MIN_WALL_THICKNESS}mm",
                severity="error",
                fix_suggestion=f"将壁厚增加到 {CNC_MIN_WALL_THICKNESS}mm 以上",
                process=process,
            ))

    elif process == ManufacturingProcess.INJECTION_MOLDING:
        if thickness < INJ_MIN_WALL_THICKNESS:
            issues.append(ManufacturingIssue(
                code="wall_too_thin",
                message=f"壁厚 {thickness}mm 低于注塑最小要求 {INJ_MIN_WALL_THICKNESS}mm",
                severity="error",
                process=process,
            ))
        if thickness > INJ_MAX_WALL_THICKNESS:
            issues.append(ManufacturingIssue(
                code="wall_too_thick",
                message=f"壁厚 {thickness}mm 超过注塑最大建议 {INJ_MAX_WALL_THICKNESS}mm",
                severity="warning",
                fix_suggestion="考虑掏空或使用加强筋减薄壁厚",
                process=process,
            ))

    return issues


def check_hole_diameter(
    diameter: float, process: str = ManufacturingProcess.FDM_3D_PRINT,
) -> list[ManufacturingIssue]:
    """检查孔径。"""
    issues: list[ManufacturingIssue] = []

    if process == ManufacturingProcess.FDM_3D_PRINT:
        if diameter < FDM_MIN_HOLE_DIAMETER:
            issues.append(ManufacturingIssue(
                code="hole_too_small",
                message=f"孔径 {diameter}mm 低于 FDM 最小可打印孔径 {FDM_MIN_HOLE_DIAMETER}mm",
                severity="error",
                fix_suggestion=f"增大孔径或打印后钻孔",
                process=process,
            ))
    elif process == ManufacturingProcess.CNC_MILLING:
        if diameter < CNC_MIN_HOLE_DIAMETER:
            issues.append(ManufacturingIssue(
                code="hole_too_small",
                message=f"孔径 {diameter}mm 低于 CNC 最小 {CNC_MIN_HOLE_DIAMETER}mm",
                severity="error",
                process=process,
            ))

    return issues


def check_overhang_angle(
    angle: float, process: str = ManufacturingProcess.FDM_3D_PRINT,
) -> list[ManufacturingIssue]:
    """检查悬垂角。"""
    issues: list[ManufacturingIssue] = []

    if process == ManufacturingProcess.FDM_3D_PRINT:
        if angle > FDM_MAX_OVERHANG_ANGLE:
            issues.append(ManufacturingIssue(
                code="overhang_too_large",
                message=f"悬垂角 {angle}° 超过安全角度 {FDM_MAX_OVERHANG_ANGLE}°",
                severity="error",
                fix_suggestion="减小悬垂角或添加支撑结构",
                process=process,
            ))

    return issues


def check_draft_angle(
    angle: float, process: str = ManufacturingProcess.INJECTION_MOLDING,
) -> list[ManufacturingIssue]:
    """检查脱模斜度（注塑）。"""
    issues: list[ManufacturingIssue] = []

    if process == ManufacturingProcess.INJECTION_MOLDING:
        if angle < INJ_MIN_DRAFT_ANGLE:
            issues.append(ManufacturingIssue(
                code="draft_too_small",
                message=f"脱模斜度 {angle}° 低于最小要求 {INJ_MIN_DRAFT_ANGLE}°",
                severity="error",
                fix_suggestion=f"增加脱模斜度到 {INJ_MIN_DRAFT_ANGLE}° 以上",
                process=process,
            ))

    return issues


def check_min_feature_size(size: float) -> list[ManufacturingIssue]:
    """检查最小特征尺寸。"""
    issues: list[ManufacturingIssue] = []
    if size < FDM_MIN_FEATURE_SIZE:
        issues.append(ManufacturingIssue(
            code="feature_too_small",
            message=f"特征尺寸 {size}mm 低于最小可打印尺寸 {FDM_MIN_FEATURE_SIZE}mm",
            severity="warning",
            fix_suggestion=f"将特征尺寸增加到 {FDM_MIN_FEATURE_SIZE}mm 以上",
        ))
    return issues


def validate_manufacturing(
    params: dict[str, Any],
    processes: list[str] | None = None,
) -> dict[str, Any]:
    """综合制造校验。

    Args:
        params: 零件参数
        processes: 要检查的制造工艺列表（默认仅 FDM）

    Returns:
        校验结果
    """
    if processes is None:
        processes = [ManufacturingProcess.FDM_3D_PRINT]

    all_issues: list[dict[str, Any]] = []
    thickness = params.get("thickness", params.get("base_thickness", 5))
    material = params.get("material", "PLA")
    hole_diameter = params.get("hole_diameter", params.get("mounting_hole_diameter", 5))

    for process in processes:
        for issue in check_wall_thickness(thickness, material, process):
            all_issues.append(issue.to_dict())

        if hole_diameter:
            for issue in check_hole_diameter(hole_diameter, process):
                all_issues.append(issue.to_dict())

        overhang = params.get("overhang_angle")
        if overhang is not None:
            for issue in check_overhang_angle(overhang, process):
                all_issues.append(issue.to_dict())

    has_error = any(i["severity"] == "error" for i in all_issues)

    return {
        "valid": not has_error,
        "issues": all_issues,
        "processes_checked": processes,
    }
