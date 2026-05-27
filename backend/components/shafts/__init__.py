"""Shafts - 轴系统。"""

from .shaft_generator import Shaft, ShaftParams
from .fit_system import get_shaft_fit, get_bearing_fit, get_gear_fit, FIT_DESCRIPTIONS

__all__ = [
    "Shaft", "ShaftParams",
    "get_shaft_fit", "get_bearing_fit", "get_gear_fit", "FIT_DESCRIPTIONS",
]
