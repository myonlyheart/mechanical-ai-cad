"""几何约束检查 - 封闭体 / 悬垂角 / 基本几何有效性"""

from .check_manufacturing import check_overhang_angle, check_geometry_closed, check_min_feature_size


def check_geometry_validity(params: dict) -> dict:
    """检查基本几何有效性"""
    all_issues: list[dict] = []

    # 基于参数推断的简单检查
    thickness = params.get("thickness", params.get("base_thickness", 5))

    # 特征尺寸检查
    if thickness < 0.5:
        for issue in check_min_feature_size(thickness):
            all_issues.append({
                "code": issue.code, "message": issue.message,
                "severity": issue.severity, "fix": issue.fix_suggestion,
            })

    has_error = any(i["severity"] == "error" for i in all_issues)

    return {
        "valid": not has_error,
        "issues": all_issues,
    }
