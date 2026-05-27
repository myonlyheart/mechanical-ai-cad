"""轴语义系统 - 轴/孔配合、轴承配合、齿轮配合。"""

from __future__ import annotations

from typing import Any

# ISO 286 公差等级 (轴径范围 -> 公差)
# 公差单位: mm
_TOLERANCE_TABLE = {
    # (min_d, max_d): {fit: (shaft_tol_low, shaft_tol_high, hole_tol_low, hole_tol_high)}
    (1, 3): {
        "H7/g6": (-0.006, -0.002, 0, +0.010),
        "H7/h6": (-0.006, 0, 0, +0.010),
        "H7/k6": (+0.001, +0.006, 0, +0.010),
        "H7/p6": (+0.010, +0.015, 0, +0.010),
        "H7/f7": (-0.016, -0.006, 0, +0.010),
        "H8/f7": (-0.016, -0.006, 0, +0.014),
    },
    (3, 6): {
        "H7/g6": (-0.009, -0.004, 0, +0.012),
        "H7/h6": (-0.008, 0, 0, +0.012),
        "H7/k6": (+0.001, +0.009, 0, +0.012),
        "H7/p6": (+0.012, +0.020, 0, +0.012),
        "H7/f7": (-0.022, -0.010, 0, +0.012),
        "H8/f7": (-0.022, -0.010, 0, +0.018),
    },
    (6, 10): {
        "H7/g6": (-0.011, -0.005, 0, +0.015),
        "H7/h6": (-0.009, 0, 0, +0.015),
        "H7/k6": (+0.001, +0.010, 0, +0.015),
        "H7/p6": (+0.015, +0.024, 0, +0.015),
        "H7/f7": (-0.028, -0.013, 0, +0.015),
        "H8/f7": (-0.028, -0.013, 0, +0.022),
    },
    (10, 18): {
        "H7/g6": (-0.014, -0.006, 0, +0.018),
        "H7/h6": (-0.011, 0, 0, +0.018),
        "H7/k6": (+0.001, +0.012, 0, +0.018),
        "H7/p6": (+0.018, +0.029, 0, +0.018),
        "H7/f7": (-0.034, -0.016, 0, +0.018),
        "H8/f7": (-0.034, -0.016, 0, +0.027),
    },
    (18, 30): {
        "H7/g6": (-0.017, -0.007, 0, +0.021),
        "H7/h6": (-0.013, 0, 0, +0.021),
        "H7/k6": (+0.002, +0.015, 0, +0.021),
        "H7/p6": (+0.022, +0.035, 0, +0.021),
        "H7/f7": (-0.041, -0.020, 0, +0.021),
        "H8/f7": (-0.041, -0.020, 0, +0.033),
    },
    (30, 50): {
        "H7/g6": (-0.020, -0.009, 0, +0.025),
        "H7/h6": (-0.016, 0, 0, +0.025),
        "H7/k6": (+0.002, +0.018, 0, +0.025),
        "H7/p6": (+0.026, +0.042, 0, +0.025),
        "H7/f7": (-0.050, -0.025, 0, +0.025),
        "H8/f7": (-0.050, -0.025, 0, +0.039),
    },
    (50, 80): {
        "H7/g6": (-0.023, -0.010, 0, +0.030),
        "H7/h6": (-0.019, 0, 0, +0.030),
        "H7/k6": (+0.002, +0.021, 0, +0.030),
        "H7/p6": (+0.032, +0.051, 0, +0.030),
        "H7/f7": (-0.060, -0.030, 0, +0.030),
        "H8/f7": (-0.060, -0.030, 0, +0.046),
    },
    (80, 120): {
        "H7/g6": (-0.027, -0.012, 0, +0.035),
        "H7/h6": (-0.022, 0, 0, +0.035),
        "H7/k6": (+0.003, +0.025, 0, +0.035),
        "H7/p6": (+0.037, +0.059, 0, +0.035),
        "H7/f7": (-0.071, -0.036, 0, +0.035),
        "H8/f7": (-0.071, -0.036, 0, +0.054),
    },
}

# 配合类型描述
FIT_DESCRIPTIONS = {
    "H7/g6": "间隙配合 - 滑动轴承、活塞",
    "H7/h6": "间隙配合 - 精密定位、可拆卸",
    "H7/k6": "过渡配合 - 齿轮、联轴器",
    "H7/p6": "过盈配合 - 轴承内圈、永久装配",
    "H7/f7": "间隙配合 - 自由旋转、油膜润滑",
    "H8/f7": "间隙配合 - 一般旋转、粗糙配合",
}

# 常用轴承系列轴径
BEARING_SERIES = {
    "6000": {"id": 10, "od": 26, "width": 8},
    "6001": {"id": 12, "od": 28, "width": 8},
    "6002": {"id": 15, "od": 32, "width": 9},
    "6003": {"id": 17, "od": 35, "width": 10},
    "6004": {"id": 20, "od": 42, "width": 12},
    "6005": {"id": 25, "od": 47, "width": 12},
    "6006": {"id": 30, "od": 55, "width": 13},
    "6007": {"id": 35, "od": 62, "width": 14},
    "6008": {"id": 40, "od": 68, "width": 15},
    "6009": {"id": 45, "od": 75, "width": 16},
    "6010": {"id": 50, "od": 80, "width": 16},
    "6200": {"id": 10, "od": 30, "width": 9},
    "6201": {"id": 12, "od": 32, "width": 10},
    "6202": {"id": 15, "od": 35, "width": 11},
    "6203": {"id": 17, "od": 40, "width": 12},
    "6204": {"id": 20, "od": 47, "width": 14},
    "6205": {"id": 25, "od": 52, "width": 15},
    "6206": {"id": 30, "od": 62, "width": 16},
    "6207": {"id": 35, "od": 72, "width": 17},
    "6208": {"id": 40, "od": 80, "width": 18},
    "6209": {"id": 45, "od": 85, "width": 19},
    "6210": {"id": 50, "od": 90, "width": 20},
}


def _get_tolerance_range(shaft_d: float) -> dict | None:
    """根据轴径找到公差范围。"""
    for (lo, hi), fits in _TOLERANCE_TABLE.items():
        if lo <= shaft_d < hi:
            return fits
    return None


def get_shaft_fit(shaft_d: float, fit_type: str = "H7/k6") -> dict[str, Any]:
    """根据轴径和配合类型返回轴/孔公差。

    Args:
        shaft_d: 轴径 (mm)
        fit_type: 配合类型，如 "H7/k6"

    Returns:
        公差信息字典
    """
    tol_range = _get_tolerance_range(shaft_d)
    if not tol_range or fit_type not in tol_range:
        # Fallback: estimate
        return {
            "shaft_diameter": shaft_d,
            "fit_type": fit_type,
            "shaft_min": shaft_d - 0.02,
            "shaft_max": shaft_d,
            "hole_min": shaft_d,
            "hole_max": shaft_d + 0.03,
            "description": FIT_DESCRIPTIONS.get(fit_type, "未知配合"),
            "clearance_min": 0.0,
            "clearance_max": 0.05,
        }

    s_lo, s_hi, h_lo, h_hi = tol_range[fit_type]
    return {
        "shaft_diameter": shaft_d,
        "fit_type": fit_type,
        "shaft_min": round(shaft_d + s_lo, 4),
        "shaft_max": round(shaft_d + s_hi, 4),
        "hole_min": round(shaft_d + h_lo, 4),
        "hole_max": round(shaft_d + h_hi, 4),
        "description": FIT_DESCRIPTIONS.get(fit_type, ""),
        "clearance_min": round(h_lo - s_hi, 4),
        "clearance_max": round(h_hi - s_lo, 4),
    }


def get_bearing_fit(shaft_d: float, bearing_series: str = "") -> dict[str, Any]:
    """轴承与轴的配合推荐。

    Args:
        shaft_d: 轴径 (mm)
        bearing_series: 轴承型号 (如 "6205")，空则自动推荐

    Returns:
        配合推荐
    """
    # Auto-recommend bearing
    if not bearing_series:
        for series, dims in sorted(BEARING_SERIES.items()):
            if dims["id"] >= shaft_d:
                bearing_series = series
                break

    bearing = BEARING_SERIES.get(bearing_series, {})
    if not bearing:
        return {
            "shaft_diameter": shaft_d,
            "bearing_series": "unknown",
            "recommendation": "未找到匹配轴承",
        }

    # 轴承内圈配合：通常过盈或过渡
    if shaft_d <= 18:
        fit = "H7/k6"       # 过渡配合
    elif shaft_d <= 50:
        fit = "H7/p6"       # 过盈配合
    else:
        fit = "H7/p6"

    fit_info = get_shaft_fit(shaft_d, fit)

    return {
        "shaft_diameter": shaft_d,
        "bearing_series": bearing_series,
        "bearing_inner_diameter": bearing["id"],
        "bearing_outer_diameter": bearing["od"],
        "bearing_width": bearing["width"],
        "recommended_fit": fit,
        "shaft_min": fit_info["shaft_min"],
        "shaft_max": fit_info["shaft_max"],
        "description": f"推荐配合: {fit} ({fit_info['description']})",
    }


def get_gear_fit(shaft_d: float, gear_module: float = 0) -> dict[str, Any]:
    """齿轮与轴的配合推荐。

    Args:
        shaft_d: 轴径 (mm)
        gear_module: 齿轮模数

    Returns:
        配合推荐
    """
    # 齿轮孔径应等于轴径
    gear_bore = shaft_d

    # 齿轮通常过渡配合 (不松不紧，可拆卸)
    if shaft_d <= 10:
        fit = "H7/k6"
    elif shaft_d <= 30:
        fit = "H7/k6"
    else:
        fit = "H7/k6"  # 齿轮一般用过渡配合

    fit_info = get_shaft_fit(shaft_d, fit)

    return {
        "shaft_diameter": shaft_d,
        "gear_bore": gear_bore,
        "gear_module": gear_module,
        "recommended_fit": fit,
        "shaft_min": fit_info["shaft_min"],
        "shaft_max": fit_info["shaft_max"],
        "hole_min": fit_info["hole_min"],
        "hole_max": fit_info["hole_max"],
        "description": f"齿轮配合: {fit} ({fit_info['description']})",
        "keyway_recommended": shaft_d >= 8,
        "keyway_width": round(shaft_d * 0.25, 1) if shaft_d >= 8 else 0,
        "keyway_depth": round(shaft_d * 0.125, 1) if shaft_d >= 8 else 0,
    }
