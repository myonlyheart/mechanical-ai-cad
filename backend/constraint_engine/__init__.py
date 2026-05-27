"""工程约束引擎 - 制造可行性 + 机械标准 + 自动修复"""

from .check_manufacturing import check_manufacturability
from .check_standard_parts import check_standards
from .check_geometry import check_geometry_validity
from .auto_fix import auto_fix


def check_and_fix(part_type: str, params: dict) -> dict:
    """完整约束检查 + 自动修复流程

    Args:
        part_type: 零件类型（bracket / gear / motor_mount / ...）
        params: 零件参数字典

    Returns:
        {
            "valid": bool,          # 修复后是否通过所有检查
            "original_params": {},  # 原始输入参数
            "fixed_params": {},     # 修复后的参数
            "issues": [],           # 所有检测到的问题
            "fixes_applied": [],    # 已执行的修复
            "checks": {}            # 各项检查的详细结果
        }
    """
    # 第一轮：收集所有问题
    all_issues: list[dict] = []

    geo_result = check_geometry_validity(params)
    mfg_result = check_manufacturability(params)
    std_result = check_standards(part_type, params)

    all_issues.extend(geo_result.get("issues", []))
    all_issues.extend(mfg_result.get("issues", []))
    all_issues.extend(std_result.get("issues", []))

    # 如果没有问题，直接返回
    if not all_issues:
        return {
            "valid": True,
            "original_params": params,
            "fixed_params": params,
            "issues": [],
            "fixes_applied": [],
            "checks": {
                "geometry": geo_result,
                "manufacturing": mfg_result,
                "standards": std_result,
            },
        }

    # 第二轮：自动修复
    error_issues = [i for i in all_issues if i.get("severity") == "error"]
    fixed_params, fixes = auto_fix(params, error_issues)

    # 第三轮：修复后重新检查
    recheck_issues: list[dict] = []
    recheck_geo = check_geometry_validity(fixed_params)
    recheck_mfg = check_manufacturability(fixed_params)
    recheck_std = check_standards(part_type, fixed_params)

    recheck_issues.extend(recheck_geo.get("issues", []))
    recheck_issues.extend(recheck_mfg.get("issues", []))
    recheck_issues.extend(recheck_std.get("issues", []))

    has_remaining_error = any(i.get("severity") == "error" for i in recheck_issues)

    return {
        "valid": not has_remaining_error,
        "original_params": params,
        "fixed_params": fixed_params,
        "issues": all_issues,
        "fixes_applied": fixes,
        "remaining_issues": recheck_issues,
        "checks": {
            "geometry": recheck_geo,
            "manufacturing": recheck_mfg,
            "standards": recheck_std,
        },
    }
