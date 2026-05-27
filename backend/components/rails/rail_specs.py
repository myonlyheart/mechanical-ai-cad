"""线性导轨规格库 - 导轨、滑块、丝杆参数。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LinearRailSpec:
    """线性导轨规格。"""
    name: str
    rail_width: float          # 导轨宽度 (mm)
    rail_height: float         # 导轨高度 (mm)
    block_width: float         # 滑块宽度 (mm)
    block_length: float        # 滑块长度 (mm)
    block_height: float        # 滑块高度 (mm)
    hole_spacing_x: float      # 滑块安装孔 X 间距 (mm)
    hole_spacing_y: float      # 滑块安装孔 Y 间距 (mm)
    hole_diameter: float       # 安装孔径 (mm)
    bore_diameter: float       # 滑块中心孔径 (mm)
    load_rating_n: float       # 额定载荷 (N)
    weight_g: float            # 滑块重量 (g)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rail_width": self.rail_width,
            "rail_height": self.rail_height,
            "block_width": self.block_width,
            "block_length": self.block_length,
            "block_height": self.block_height,
            "hole_spacing_x": self.hole_spacing_x,
            "hole_spacing_y": self.hole_spacing_y,
            "hole_diameter": self.hole_diameter,
            "bore_diameter": self.bore_diameter,
            "load_rating_n": self.load_rating_n,
            "weight_g": self.weight_g,
        }


@dataclass
class LeadScrewSpec:
    """丝杆规格。"""
    name: str
    diameter: float            # 丝杆直径 (mm)
    pitch: float               # 螺距 (mm)
    lead: float                # 导程 (mm)
    starts: int                # 头数
    nut_outer_diameter: float  # 螺母外径 (mm)
    nut_length: float          # 螺母长度 (mm)
    nut_flange_diameter: float # 螺母法兰直径 (mm)
    nut_hole_spacing: float    # 螺母安装孔间距 (mm)
    nut_hole_diameter: float   # 螺母安装孔径 (mm)
    efficiency: float          # 传动效率
    backlash_mm: float         # 回程间隙 (mm)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "diameter": self.diameter,
            "pitch": self.pitch,
            "lead": self.lead,
            "starts": self.starts,
            "nut_outer_diameter": self.nut_outer_diameter,
            "nut_length": self.nut_length,
            "nut_flange_diameter": self.nut_flange_diameter,
            "nut_hole_spacing": self.nut_hole_spacing,
            "nut_hole_diameter": self.nut_hole_diameter,
            "efficiency": self.efficiency,
            "backlash_mm": self.backlash_mm,
        }


# 线性导轨规格库
LINEAR_RAILS: dict[str, LinearRailSpec] = {
    "MGN7": LinearRailSpec(
        name="MGN7", rail_width=7, rail_height=5.2,
        block_width=17, block_length=13.7, block_height=6.5,
        hole_spacing_x=9.6, hole_spacing_y=6.5, hole_diameter=1.4,
        bore_diameter=0, load_rating_n=340, weight_g=8,
    ),
    "MGN9": LinearRailSpec(
        name="MGN9", rail_width=9, rail_height=6.5,
        block_width=20, block_length=17.5, block_height=8,
        hole_spacing_x=12.5, hole_spacing_y=8, hole_diameter=2.2,
        bore_diameter=0, load_rating_n=580, weight_g=15,
    ),
    "MGN12": LinearRailSpec(
        name="MGN12", rail_width=12, rail_height=8,
        block_width=27, block_length=23, block_height=10,
        hole_spacing_x=16, hole_spacing_y=10, hole_diameter=2.6,
        bore_diameter=0, load_rating_n=1100, weight_g=28,
    ),
    "MGN15": LinearRailSpec(
        name="MGN15", rail_width=15, rail_height=9.5,
        block_width=32, block_length=27, block_height=12,
        hole_spacing_x=20, hole_spacing_y=12, hole_diameter=3.2,
        bore_diameter=0, load_rating_n=1800, weight_g=50,
    ),
    "HGR15": LinearRailSpec(
        name="HGR15", rail_width=15, rail_height=12.5,
        block_width=34, block_length=34.4, block_height=16,
        hole_spacing_x=26, hole_spacing_y=16, hole_diameter=3.5,
        bore_diameter=0, load_rating_n=6000, weight_g=120,
    ),
    "HGR20": LinearRailSpec(
        name="HGR20", rail_width=20, rail_height=15.5,
        block_width=44, block_length=42.4, block_height=20,
        hole_spacing_x=32, hole_spacing_y=20, hole_diameter=4.5,
        bore_diameter=0, load_rating_n=13000, weight_g=250,
    ),
}


# 丝杆规格库
LEAD_SCREWS: dict[str, LeadScrewSpec] = {
    "T8x2": LeadScrewSpec(
        name="T8x2", diameter=8, pitch=2, lead=2, starts=1,
        nut_outer_diameter=22, nut_length=12, nut_flange_diameter=30,
        nut_hole_spacing=24, nut_hole_diameter=3.4,
        efficiency=0.3, backlash_mm=0.05,
    ),
    "T8x4": LeadScrewSpec(
        name="T8x4", diameter=8, pitch=2, lead=4, starts=2,
        nut_outer_diameter=22, nut_length=12, nut_flange_diameter=30,
        nut_hole_spacing=24, nut_hole_diameter=3.4,
        efficiency=0.35, backlash_mm=0.05,
    ),
    "T8x8": LeadScrewSpec(
        name="T8x8", diameter=8, pitch=2, lead=8, starts=4,
        nut_outer_diameter=22, nut_length=12, nut_flange_diameter=30,
        nut_hole_spacing=24, nut_hole_diameter=3.4,
        efficiency=0.4, backlash_mm=0.08,
    ),
    "SFU1204": LeadScrewSpec(
        name="SFU1204", diameter=12, pitch=4, lead=4, starts=1,
        nut_outer_diameter=22, nut_length=14, nut_flange_diameter=32,
        nut_hole_spacing=26, nut_hole_diameter=3.4,
        efficiency=0.9, backlash_mm=0.02,
    ),
    "SFU1605": LeadScrewSpec(
        name="SFU1605", diameter=16, pitch=5, lead=5, starts=1,
        nut_outer_diameter=28, nut_length=16, nut_flange_diameter=42,
        nut_hole_spacing=32, nut_hole_diameter=4.5,
        efficiency=0.9, backlash_mm=0.02,
    ),
    "SFU2005": LeadScrewSpec(
        name="SFU2005", diameter=20, pitch=5, lead=5, starts=1,
        nut_outer_diameter=36, nut_length=18, nut_flange_diameter=52,
        nut_hole_spacing=40, nut_hole_diameter=5.5,
        efficiency=0.9, backlash_mm=0.015,
    ),
}


def get_rail_spec(rail_name: str) -> LinearRailSpec | None:
    return LINEAR_RAILS.get(rail_name)


def get_screw_spec(screw_name: str) -> LeadScrewSpec | None:
    return LEAD_SCREWS.get(screw_name)


def list_rails() -> list[dict[str, Any]]:
    return [s.to_dict() for s in LINEAR_RAILS.values()]


def list_screws() -> list[dict[str, Any]]:
    return [s.to_dict() for s in LEAD_SCREWS.values()]


def calculate_travel(rail_length: float, block_length: float) -> float:
    """计算有效行程。

    Args:
        rail_length: 导轨总长 (mm)
        block_length: 滑块长度 (mm)

    Returns:
        有效行程 (mm)
    """
    return max(0, rail_length - block_length)


def calculate_steps_per_mm(screw_name: str, stepper_angle: float = 1.8, microstepping: int = 16) -> float:
    """计算每毫米步进数。

    Args:
        screw_name: 丝杆名称
        stepper_angle: 步进电机步进角 (度)
        microstepping: 细分数

    Returns:
        每毫米需要的步进数
    """
    spec = LEAD_SCREWS.get(screw_name)
    if not spec:
        return 0
    steps_per_rev = 360.0 / stepper_angle * microstepping
    return steps_per_rev / spec.lead
