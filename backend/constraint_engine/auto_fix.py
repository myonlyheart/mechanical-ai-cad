"""自动修复逻辑 - 检测到问题后自动调整参数"""

from .check_manufacturing import FDM_MIN_WALL_THICKNESS, FDM_MIN_HOLE_DIAMETER, FDM_MAX_OVERHANG_ANGLE
from .check_standard_parts import METRIC_CLEARANCE_HOLES, NEMA_STANDARDS, BEARING_STANDARDS


# 修复规则：问题代码 → 修复函数
def fix_wall_too_thin(params: dict) -> tuple[dict, str]:
    """自动增加壁厚到安全值"""
    new_params = dict(params)
    min_safe = max(FDM_MIN_WALL_THICKNESS * 1.5, 2.0)

    # 适配不同参数名
    for key in ("thickness", "base_thickness", "wall_thickness"):
        if key in new_params and new_params[key] < min_safe:
            new_params[key] = min_safe
            return new_params, f"{key} 已从 {params[key]}mm 调整为 {min_safe}mm"

    # 如果没找到对应字段，默认设置 thickness
    new_params["thickness"] = min_safe
    return new_params, f"thickness 已设置为 {min_safe}mm"


def fix_hole_too_small(params: dict) -> tuple[dict, str]:
    """自动增大孔径到最小可打印值"""
    new_params = dict(params)
    screw = params.get("screw", "")

    if screw and screw in METRIC_CLEARANCE_HOLES:
        std_dia = METRIC_CLEARANCE_HOLES[screw]["diameter"]
        target = std_dia + 0.3  # 打印补偿
    else:
        target = FDM_MIN_HOLE_DIAMETER + 0.5

    for key in ("hole_diameter", "mounting_hole_diameter"):
        if key in new_params and new_params[key] < target:
            old = new_params[key]
            new_params[key] = round(target, 1)
            return new_params, f"{key} 已从 {old}mm 调整为 {new_params[key]}mm"

    return new_params, ""


def fix_screw_hole_too_small(params: dict) -> tuple[dict, str]:
    """按螺栓标准修复孔径"""
    new_params = dict(params)
    screw = params.get("screw", "")

    if screw in METRIC_CLEARANCE_HOLES:
        target = METRIC_CLEARANCE_HOLES[screw]["diameter"] + 0.3
        for key in ("hole_diameter", "mounting_hole_diameter"):
            if key in new_params:
                old = new_params[key]
                new_params[key] = round(target, 1)
                return new_params, f"{key} 已从 {old}mm 调整为 {new_params[key]}mm（{screw} 标准）"

    return new_params, ""


def fix_nema_hole_spacing_wrong(params: dict) -> tuple[dict, str]:
    """按 NEMA 标准修复安装孔间距"""
    new_params = dict(params)
    motor = params.get("motor_type", "")

    if motor in NEMA_STANDARDS:
        target = NEMA_STANDARDS[motor]["mounting_hole_spacing"]
        new_params["motor_hole_spacing"] = target
        return new_params, f"motor_hole_spacing 已调整为 {target}mm（{motor} 标准）"

    return new_params, ""


def fix_nema_hole_too_small(params: dict) -> tuple[dict, str]:
    """按 NEMA 标准修复安装孔径"""
    new_params = dict(params)
    motor = params.get("motor_type", "")

    if motor in NEMA_STANDARDS:
        target = NEMA_STANDARDS[motor]["mounting_hole_diameter"] + 0.3
        new_params["mounting_hole_diameter"] = round(target, 1)
        return new_params, f"mounting_hole_diameter 已调整为 {target}mm（{motor} 标准）"

    return new_params, ""


def fix_nema_center_bore_too_small(params: dict) -> tuple[dict, str]:
    """按 NEMA 标准修复中心孔"""
    new_params = dict(params)
    motor = params.get("motor_type", "")

    if motor in NEMA_STANDARDS:
        target = NEMA_STANDARDS[motor]["center_bore_diameter"]
        new_params["center_bore"] = target
        return new_params, f"center_bore 已调整为 {target}mm（{motor} 标准）"

    return new_params, ""


def fix_bearing_bore_too_small(params: dict) -> tuple[dict, str]:
    """按轴承标准修复安装孔"""
    new_params = dict(params)
    bearing = params.get("bearing", "")

    if bearing in BEARING_STANDARDS:
        target = BEARING_STANDARDS[bearing]["housing_bore"]
        for key in ("hole_diameter", "housing_bore"):
            if key in new_params:
                new_params[key] = round(target, 2)
                return new_params, f"{key} 已调整为 {target}mm（{bearing} 轴承标准）"

    return new_params, ""


# 修复路由表
FIX_ROUTES = {
    "wall_too_thin": fix_wall_too_thin,
    "hole_too_small": fix_hole_too_small,
    "screw_hole_too_small": fix_screw_hole_too_small,
    "nema_hole_spacing_wrong": fix_nema_hole_spacing_wrong,
    "nema_hole_too_small": fix_nema_hole_too_small,
    "nema_center_bore_too_small": fix_nema_center_bore_too_small,
    "bearing_bore_too_small": fix_bearing_bore_too_small,
}


def auto_fix(params: dict, issues: list[dict]) -> tuple[dict, list[str]]:
    """根据检测到的问题列表，自动修复参数

    返回：(修复后的参数, 修复说明列表)
    """
    current_params = dict(params)
    fixes_applied: list[str] = []

    for issue in issues:
        code = issue.get("code", "")
        if code in FIX_ROUTES:
            fixer = FIX_ROUTES[code]
            current_params, fix_msg = fixer(current_params)
            if fix_msg:
                fixes_applied.append(fix_msg)

    return current_params, fixes_applied
