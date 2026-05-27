"""Gears - 齿轮系统。"""

from .gear_generator import Gear, GearParams
from .drive_system import (
    calculate_center_distance, calculate_gear_ratio,
    auto_select_gears, calculate_mesh_position,
)

__all__ = [
    "Gear", "GearParams",
    "calculate_center_distance", "calculate_gear_ratio",
    "auto_select_gears", "calculate_mesh_position",
]
