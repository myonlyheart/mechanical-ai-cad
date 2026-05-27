"""Auto drive system - 自动传动系统。"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd, pi
from typing import Any


@dataclass
class DriveGear:
    """传动齿轮。"""
    tooth_count: int = 20
    module: float = 2.0
    position: tuple[float, float, float] = (0, 0, 0)
    pitch_radius: float = 0.0

    def __post_init__(self):
        if self.pitch_radius == 0:
            self.pitch_radius = (self.module * self.tooth_count) / 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "tooth_count": self.tooth_count,
            "module": self.module,
            "pitch_radius": round(self.pitch_radius, 2),
            "position": [round(c, 2) for c in self.position],
        }


@dataclass
class DriveSystem:
    """传动系统方案。"""
    ratio: float = 1.0
    actual_ratio: float = 1.0
    module: float = 2.0
    stages: list[dict[str, Any]] = field(default_factory=list)
    center_distances: list[float] = field(default_factory=list)
    total_gears: int = 0
    input_speed_ratio: float = 1.0
    output_speed_ratio: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_ratio": round(self.ratio, 4),
            "actual_ratio": round(self.actual_ratio, 4),
            "module": self.module,
            "stages": self.stages,
            "center_distances": [round(cd, 2) for cd in self.center_distances],
            "total_gears": self.total_gears,
            "input_speed_ratio": self.input_speed_ratio,
            "output_speed_ratio": self.output_speed_ratio,
        }


def calculate_center_distance(module: float, teeth_a: int, teeth_b: int) -> float:
    """计算两齿轮中心距。

    Args:
        module: 模数
        teeth_a: 齿轮A齿数
        teeth_b: 齿轮B齿数

    Returns:
        中心距 (mm)
    """
    return module * (teeth_a + teeth_b) / 2


def calculate_gear_ratio(teeth_driver: int, teeth_driven: int) -> float:
    """计算传动比。

    Args:
        teeth_driver: 主动轮齿数
        teeth_driven: 从动轮齿数

    Returns:
        传动比 (从动/主动，>1 减速，<1 增速)
    """
    return teeth_driven / teeth_driver


def auto_select_gears(
    target_ratio: float,
    module: float = 2.0,
    min_teeth: int = 12,
    max_teeth: int = 80,
    max_stages: int = 2,
) -> DriveSystem:
    """自动选择齿轮组合实现目标传动比。

    Args:
        target_ratio: 目标传动比 (>1 减速，<1 增速)
        module: 模数
        min_teeth: 最小齿数
        max_teeth: 最大齿数
        max_stages: 最大级数

    Returns:
        DriveSystem 方案
    """
    system = DriveSystem(ratio=target_ratio, module=module)

    if target_ratio <= 0:
        return system

    # Single stage: find best pair
    if target_ratio <= max_teeth / min_teeth:
        best = _find_best_pair(target_ratio, min_teeth, max_teeth)
        if best:
            t1, t2 = best
            cd = calculate_center_distance(module, t1, t2)
            system.stages.append({
                "stage": 1,
                "driver": {"tooth_count": t1, "pitch_radius": module * t1 / 2},
                "driven": {"tooth_count": t2, "pitch_radius": module * t2 / 2},
                "ratio": round(t2 / t1, 4),
                "center_distance": round(cd, 2),
            })
            system.center_distances.append(cd)
            system.actual_ratio = t2 / t1
            system.total_gears = 2
    else:
        # Multi-stage: split ratio
        if max_stages >= 2:
            split_ratio = target_ratio ** 0.5  # equal split
            best1 = _find_best_pair(split_ratio, min_teeth, max_teeth)
            if best1:
                t1, t2 = best1
                remaining = target_ratio / (t2 / t1)
                best2 = _find_best_pair(remaining, min_teeth, max_teeth)
                if best2:
                    t3, t4 = best2
                    cd1 = calculate_center_distance(module, t1, t2)
                    cd2 = calculate_center_distance(module, t3, t4)
                    system.stages = [
                        {
                            "stage": 1,
                            "driver": {"tooth_count": t1, "pitch_radius": module * t1 / 2},
                            "driven": {"tooth_count": t2, "pitch_radius": module * t2 / 2},
                            "ratio": round(t2 / t1, 4),
                            "center_distance": round(cd1, 2),
                        },
                        {
                            "stage": 2,
                            "driver": {"tooth_count": t3, "pitch_radius": module * t3 / 2},
                            "driven": {"tooth_count": t4, "pitch_radius": module * t4 / 2},
                            "ratio": round(t4 / t3, 4),
                            "center_distance": round(cd2, 2),
                        },
                    ]
                    system.center_distances = [cd1, cd2]
                    system.actual_ratio = (t2 / t1) * (t4 / t3)
                    system.total_gears = 4

    system.input_speed_ratio = 1.0
    system.output_speed_ratio = 1.0 / system.actual_ratio if system.actual_ratio > 0 else 1.0
    return system


def _find_best_pair(target_ratio: float, min_teeth: int, max_teeth: int) -> tuple[int, int] | None:
    """Find the best (driver, driven) pair closest to target ratio."""
    best_pair = None
    best_error = float("inf")

    for t1 in range(min_teeth, min(max_teeth + 1, 60)):
        t2_ideal = target_ratio * t1
        t2 = round(t2_ideal)
        if min_teeth <= t2 <= max_teeth:
            error = abs(t2 / t1 - target_ratio)
            if error < best_error:
                best_error = error
                best_pair = (t1, t2)

    return best_pair


def calculate_mesh_position(
    gear_a: DriveGear,
    gear_b: DriveGear,
    offset_angle: float = 0.0,
) -> tuple[float, float, float]:
    """计算齿轮B的啮合位置（相对于齿轮A）。

    Args:
        gear_a: 驱动齿轮
        gear_b: 被动齿轮
        offset_angle: 安装角度偏移 (degrees)

    Returns:
        齿轮B的 (x, y, z) 位置
    """
    import math
    cd = calculate_center_distance(gear_a.module, gear_a.tooth_count, gear_b.tooth_count)
    angle_rad = math.radians(offset_angle)
    x = gear_a.position[0] + cd * math.cos(angle_rad)
    y = gear_a.position[1] + cd * math.sin(angle_rad)
    z = gear_a.position[2]
    return (x, y, z)
