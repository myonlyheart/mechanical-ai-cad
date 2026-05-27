"""Automatic screw hole matching - 自动螺丝孔匹配。"""

from __future__ import annotations

from typing import Any

# ISO 273 通孔标准 (bolt diameter -> clearance hole)
CLEARANCE_HOLES = {
    3: {"close": 3.2, "normal": 3.4, "loose": 3.6},
    4: {"close": 4.3, "normal": 4.5, "loose": 4.8},
    5: {"close": 5.3, "normal": 5.5, "loose": 5.8},
    6: {"close": 6.4, "normal": 6.6, "loose": 7.0},
    8: {"close": 8.4, "normal": 9.0, "loose": 10.0},
    10: {"close": 10.5, "normal": 11.0, "loose": 12.0},
    12: {"close": 13.0, "normal": 13.5, "loose": 14.5},
    16: {"close": 17.0, "normal": 17.5, "loose": 18.5},
    20: {"close": 21.0, "normal": 22.0, "loose": 24.0},
}

# 螺纹底孔 (bolt diameter -> tap drill)
TAP_DRILLS = {
    3: 2.5,
    4: 3.3,
    5: 4.2,
    6: 5.0,
    8: 6.8,
    10: 8.5,
    12: 10.2,
    16: 14.0,
    20: 17.5,
}

# 内六角头尺寸
SOCKET_HEAD_DIMS = {
    3: {"diameter": 5.5, "height": 3.0},
    4: {"diameter": 7.0, "height": 4.0},
    5: {"diameter": 8.5, "height": 5.0},
    6: {"diameter": 10.0, "height": 6.0},
    8: {"diameter": 13.0, "height": 8.0},
    10: {"diameter": 16.0, "height": 10.0},
    12: {"diameter": 18.0, "height": 12.0},
    16: {"diameter": 24.0, "height": 16.0},
    20: {"diameter": 30.0, "height": 20.0},
}


def get_hole_diameter(bolt_diameter: float, hole_type: str = "normal") -> float:
    """计算螺丝孔径。

    Args:
        bolt_diameter: 螺栓公称直径 (mm)
        hole_type: "close"(紧配), "normal"(标准通孔), "loose"(松配), "tapped"(螺纹孔)

    Returns:
        孔径 (mm)
    """
    d = int(bolt_diameter)
    if hole_type == "tapped":
        return TAP_DRILLS.get(d, bolt_diameter * 0.85)
    fits = CLEARANCE_HOLES.get(d)
    if fits:
        return fits.get(hole_type, fits["normal"])
    # Fallback for non-standard sizes
    if hole_type == "close":
        return bolt_diameter + 0.2
    elif hole_type == "loose":
        return bolt_diameter + 1.0
    return bolt_diameter + 0.5


def get_counterbore_dimensions(bolt_diameter: float, head_type: str = "socket") -> dict[str, float]:
    """计算台阶孔尺寸。

    Args:
        bolt_diameter: 螺栓公称直径
        head_type: "socket"(内六角), "hex"(六角头)

    Returns:
        {"diameter": 台阶孔径, "depth": 台阶深度}
    """
    d = int(bolt_diameter)
    if head_type == "socket":
        dims = SOCKET_HEAD_DIMS.get(d, {"diameter": bolt_diameter * 1.6, "height": bolt_diameter})
        return {
            "diameter": dims["diameter"] + 0.5,
            "depth": dims["height"] + 0.5,
        }
    elif head_type == "hex":
        from .bolt_generator import HEX_HEAD_DIMS
        dims = HEX_HEAD_DIMS.get(d, {"across_flats": bolt_diameter * 1.8, "height": bolt_diameter * 0.7})
        # Counterbore for hex: cylindrical pocket
        circum_r = dims["across_flats"] / 0.866 / 2
        return {
            "diameter": circum_r * 2 + 0.5,
            "depth": dims["height"] + 0.5,
        }
    return {"diameter": bolt_diameter * 1.6, "depth": bolt_diameter}


def get_countersink_diameter(bolt_diameter: float) -> float:
    """计算沉头孔直径。

    Args:
        bolt_diameter: 螺栓公称直径

    Returns:
        沉头孔直径 (mm)
    """
    d = int(bolt_diameter)
    dims = SOCKET_HEAD_DIMS.get(d, {"diameter": bolt_diameter * 1.6})
    # Countersink: slightly larger than head
    return dims["diameter"] + 0.5


def recommend_bolt(hole_diameter: float) -> dict[str, Any]:
    """根据孔径推荐螺栓规格。

    Args:
        hole_diameter: 孔径 (mm)

    Returns:
        {"diameter": 公称直径, "fit": 配合类型, "hole_type": 孔类型}
    """
    best_d = None
    best_fit = "normal"
    min_diff = float("inf")

    for d, fits in CLEARANCE_HOLES.items():
        for fit_name, fit_d in fits.items():
            diff = abs(fit_d - hole_diameter)
            if diff < min_diff:
                min_diff = diff
                best_d = d
                best_fit = fit_name

    if best_d is None:
        return {"diameter": round(hole_diameter - 0.5), "fit": "normal", "hole_type": "clearance"}

    return {"diameter": best_d, "fit": best_fit, "hole_type": "clearance"}
