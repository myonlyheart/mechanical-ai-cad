"""标准零件约束检查 - M螺栓 / NEMA电机 / 轴承标准"""

from dataclasses import dataclass

# M 螺栓标准孔径（mm）- 间隙配合
METRIC_CLEARANCE_HOLES = {
    "M2":  {"diameter": 2.4, "head_diameter": 4.0, "head_height": 1.6},
    "M2.5": {"diameter": 3.0, "head_diameter": 5.0, "head_height": 2.0},
    "M3":  {"diameter": 3.4, "head_diameter": 5.5, "head_height": 2.0},
    "M4":  {"diameter": 4.5, "head_diameter": 7.0, "head_height": 2.8},
    "M5":  {"diameter": 5.5, "head_diameter": 8.5, "head_height": 3.5},
    "M6":  {"diameter": 6.6, "head_diameter": 10.0, "head_height": 4.0},
    "M8":  {"diameter": 9.0, "head_diameter": 13.0, "head_height": 5.3},
}

# NEMA 电机标准尺寸（mm）
NEMA_STANDARDS = {
    "NEMA17": {
        "body_size": 42.3,
        "mounting_hole_spacing": 31.0,
        "mounting_hole_diameter": 3.4,
        "shaft_diameter": 5.0,
        "shaft_length": 24.0,
        "center_bore_diameter": 22.0,
    },
    "NEMA23": {
        "body_size": 56.4,
        "mounting_hole_spacing": 47.1,
        "mounting_hole_diameter": 5.0,
        "shaft_diameter": 6.35,
        "shaft_length": 25.0,
        "center_bore_diameter": 38.1,
    },
    "NEMA34": {
        "body_size": 86.0,
        "mounting_hole_spacing": 69.6,
        "mounting_hole_diameter": 5.5,
        "shaft_diameter": 14.0,
        "shaft_length": 37.0,
        "center_bore_diameter": 73.0,
    },
}

# 常用轴承标准（mm）
BEARING_STANDARDS = {
    "608": {
        "outer_diameter": 22.0,
        "inner_diameter": 8.0,
        "width": 7.0,
        "housing_bore": 22.0 + 0.02,  # 过盈配合
        "shaft_seat": 8.0 - 0.01,
    },
    "625": {
        "outer_diameter": 16.0,
        "inner_diameter": 5.0,
        "width": 5.0,
        "housing_bore": 16.0 + 0.02,
        "shaft_seat": 5.0 - 0.01,
    },
    "6001": {
        "outer_diameter": 28.0,
        "inner_diameter": 12.0,
        "width": 8.0,
        "housing_bore": 28.0 + 0.02,
        "shaft_seat": 12.0 - 0.01,
    },
}


@dataclass
class StandardPartIssue:
    code: str
    message: str
    severity: str = "error"
    fix_suggestion: str = ""


def check_screw_hole(screw: str, hole_diameter: float) -> list[StandardPartIssue]:
    """检查螺栓孔径是否符合标准"""
    issues = []
    standard = METRIC_CLEARANCE_HOLES.get(screw)

    if not standard:
        issues.append(StandardPartIssue(
            code="unknown_screw",
            message=f"未知螺栓规格: {screw}",
            severity="warning",
            fix_suggestion=f"支持的规格: {', '.join(METRIC_CLEARANCE_HOLES.keys())}",
        ))
        return issues

    std_dia = standard["diameter"]
    tolerance = 0.5  # FDM 打印公差

    if hole_diameter < std_dia - tolerance:
        issues.append(StandardPartIssue(
            code="screw_hole_too_small",
            message=f"{screw} 标准孔径为 {std_dia}mm，当前 {hole_diameter}mm 过小，螺栓无法穿过",
            severity="error",
            fix_suggestion=f"将孔径调整为 {std_dia + 0.3}mm（含打印补偿）",
        ))
    elif hole_diameter > std_dia + 1.0:
        issues.append(StandardPartIssue(
            code="screw_hole_too_large",
            message=f"{screw} 孔径 {hole_diameter}mm 过大，螺栓会松动",
            severity="warning",
            fix_suggestion=f"将孔径调整为 {std_dia + 0.3}mm",
        ))

    return issues


def check_nema_mount(motor_type: str, params: dict) -> list[StandardPartIssue]:
    """检查 NEMA 电机安装尺寸"""
    issues = []
    standard = NEMA_STANDARDS.get(motor_type)

    if not standard:
        issues.append(StandardPartIssue(
            code="unknown_motor",
            message=f"未知电机规格: {motor_type}",
            severity="warning",
            fix_suggestion=f"支持的规格: {', '.join(NEMA_STANDARDS.keys())}",
        ))
        return issues

    # 检查安装孔间距
    expected_spacing = standard["mounting_hole_spacing"]
    actual_spacing = params.get("motor_hole_spacing", expected_spacing)
    if abs(actual_spacing - expected_spacing) > 0.5:
        issues.append(StandardPartIssue(
            code="nema_hole_spacing_wrong",
            message=f"{motor_type} 安装孔间距应为 {expected_spacing}mm，当前为 {actual_spacing}mm",
            severity="error",
            fix_suggestion=f"将 motor_hole_spacing 设为 {expected_spacing}",
        ))

    # 检查安装孔径
    expected_hole = standard["mounting_hole_diameter"]
    actual_hole = params.get("mounting_hole_diameter", expected_hole)
    if actual_hole < expected_hole - 0.3:
        issues.append(StandardPartIssue(
            code="nema_hole_too_small",
            message=f"{motor_type} 安装孔径 {actual_hole}mm 小于标准 {expected_hole}mm",
            severity="error",
            fix_suggestion=f"将 mounting_hole_diameter 设为 {expected_hole + 0.3}",
        ))

    # 检查中心孔
    expected_center = standard["center_bore_diameter"]
    actual_center = params.get("center_bore", params.get("center_bore_diameter", expected_center))
    if actual_center < expected_center - 1.0:
        issues.append(StandardPartIssue(
            code="nema_center_bore_too_small",
            message=f"{motor_type} 中心孔径 {actual_center}mm 小于标准 {expected_center}mm，转轴可能无法穿过",
            severity="error",
            fix_suggestion=f"将 center_bore 设为 {expected_center}",
        ))

    return issues


def check_bearing_fit(bearing: str, hole_diameter: float) -> list[StandardPartIssue]:
    """检查轴承安装孔尺寸"""
    issues = []
    standard = BEARING_STANDARDS.get(bearing)

    if not standard:
        issues.append(StandardPartIssue(
            code="unknown_bearing",
            message=f"未知轴承规格: {bearing}",
            severity="warning",
            fix_suggestion=f"支持的规格: {', '.join(BEARING_STANDARDS.keys())}",
        ))
        return issues

    expected_bore = standard["housing_bore"]
    tolerance = 0.3  # 3D 打印宽松公差

    if hole_diameter < expected_bore - tolerance:
        issues.append(StandardPartIssue(
            code="bearing_bore_too_small",
            message=f"{bearing} 轴承外径 {standard['outer_diameter']}mm，安装孔 {hole_diameter}mm 过小",
            severity="error",
            fix_suggestion=f"将安装孔直径设为 {expected_bore}mm",
        ))
    elif hole_diameter > expected_bore + 0.5:
        issues.append(StandardPartIssue(
            code="bearing_bore_too_large",
            message=f"{bearing} 安装孔 {hole_diameter}mm 过大，轴承会松动",
            severity="warning",
            fix_suggestion=f"将安装孔直径设为 {expected_bore}mm",
        ))

    return issues


def check_standards(part_type: str, params: dict) -> dict:
    """综合标准零件检查"""
    all_issues: list[dict] = []

    screw = params.get("screw", "")
    hole_dia = params.get("hole_diameter", params.get("mounting_hole_diameter", 0))
    bearing = params.get("bearing", "")
    motor = params.get("motor_type", "")

    if screw and hole_dia:
        for issue in check_screw_hole(screw, hole_dia):
            all_issues.append({"code": issue.code, "message": issue.message, "severity": issue.severity, "fix": issue.fix_suggestion})

    if motor:
        for issue in check_nema_mount(motor, params):
            all_issues.append({"code": issue.code, "message": issue.message, "severity": issue.severity, "fix": issue.fix_suggestion})

    if bearing and hole_dia:
        for issue in check_bearing_fit(bearing, hole_dia):
            all_issues.append({"code": issue.code, "message": issue.message, "severity": issue.severity, "fix": issue.fix_suggestion})

    has_error = any(i["severity"] == "error" for i in all_issues)

    return {
        "valid": not has_error,
        "issues": all_issues,
    }
