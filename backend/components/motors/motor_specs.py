"""电机规格库 - 电机参数、安装尺寸、联轴器推荐。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MotorSpec:
    """电机规格定义。"""
    name: str
    motor_type: str               # stepper, dc, servo
    body_size: float              # 机身尺寸 (mm, 正方形边长)
    body_length: float            # 机身长度 (mm)
    mounting_hole_spacing: float  # 安装孔间距 (mm)
    mounting_hole_diameter: float # 安装孔径 (mm)
    mounting_hole_count: int      # 安装孔数量
    shaft_diameter: float         # 轴径 (mm)
    shaft_length: float           # 轴长 (mm)
    center_bore_diameter: float   # 中心凸台直径 (mm)
    weight_g: float               # 重量 (g)
    voltage: float = 12.0         # 额定电压 (V)
    current_a: float = 1.5        # 额定电流 (A)
    torque_nm: float = 0.4        # 保持力矩 (Nm)
    step_angle: float = 1.8       # 步进角 (度)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "motor_type": self.motor_type,
            "body_size": self.body_size,
            "body_length": self.body_length,
            "mounting_hole_spacing": self.mounting_hole_spacing,
            "mounting_hole_diameter": self.mounting_hole_diameter,
            "mounting_hole_count": self.mounting_hole_count,
            "shaft_diameter": self.shaft_diameter,
            "shaft_length": self.shaft_length,
            "center_bore_diameter": self.center_bore_diameter,
            "weight_g": self.weight_g,
            "voltage": self.voltage,
            "current_a": self.current_a,
            "torque_nm": self.torque_nm,
            "step_angle": self.step_angle,
        }


# 电机规格数据库
MOTOR_SPECS: dict[str, MotorSpec] = {
    "NEMA17": MotorSpec(
        name="NEMA17",
        motor_type="stepper",
        body_size=42.3,
        body_length=40.0,
        mounting_hole_spacing=31.0,
        mounting_hole_diameter=3.4,
        mounting_hole_count=4,
        shaft_diameter=5.0,
        shaft_length=24.0,
        center_bore_diameter=22.0,
        weight_g=280,
        voltage=12.0,
        current_a=1.5,
        torque_nm=0.4,
        step_angle=1.8,
    ),
    "NEMA17_long": MotorSpec(
        name="NEMA17 (48mm)",
        motor_type="stepper",
        body_size=42.3,
        body_length=48.0,
        mounting_hole_spacing=31.0,
        mounting_hole_diameter=3.4,
        mounting_hole_count=4,
        shaft_diameter=5.0,
        shaft_length=24.0,
        center_bore_diameter=22.0,
        weight_g=350,
        voltage=12.0,
        current_a=2.0,
        torque_nm=0.59,
        step_angle=1.8,
    ),
    "NEMA23": MotorSpec(
        name="NEMA23",
        motor_type="stepper",
        body_size=56.4,
        body_length=51.0,
        mounting_hole_spacing=47.1,
        mounting_hole_diameter=5.0,
        mounting_hole_count=4,
        shaft_diameter=6.35,
        shaft_length=25.0,
        center_bore_diameter=38.1,
        weight_g=700,
        voltage=24.0,
        current_a=3.0,
        torque_nm=1.26,
        step_angle=1.8,
    ),
    "NEMA34": MotorSpec(
        name="NEMA34",
        motor_type="stepper",
        body_size=86.0,
        body_length=76.0,
        mounting_hole_spacing=69.6,
        mounting_hole_diameter=5.5,
        mounting_hole_count=4,
        shaft_diameter=14.0,
        shaft_length=37.0,
        center_bore_diameter=73.0,
        weight_g=2800,
        voltage=36.0,
        current_a=5.0,
        torque_nm=4.5,
        step_angle=1.8,
    ),
    "775": MotorSpec(
        name="775电机",
        motor_type="dc",
        body_size=42.0,
        body_length=66.0,
        mounting_hole_spacing=25.0,
        mounting_hole_diameter=4.5,
        mounting_hole_count=4,
        shaft_diameter=5.0,
        shaft_length=17.0,
        center_bore_diameter=0,
        weight_g=340,
        voltage=12.0,
        current_a=1.5,
        torque_nm=0.05,
        step_angle=0,  # DC 电机无步进角
    ),
    "SG90": MotorSpec(
        name="SG90 舵机",
        motor_type="servo",
        body_size=23.0,
        body_length=12.5,
        mounting_hole_spacing=28.0,
        mounting_hole_diameter=2.2,
        mounting_hole_count=4,
        shaft_diameter=4.8,
        shaft_length=5.0,
        center_bore_diameter=0,
        weight_g=9,
        voltage=5.0,
        current_a=0.1,
        torque_nm=0.018,
        step_angle=0,
    ),
    "MG996R": MotorSpec(
        name="MG996R 舵机",
        motor_type="servo",
        body_size=40.0,
        body_length=19.5,
        mounting_hole_spacing=49.5,
        mounting_hole_diameter=4.2,
        mounting_hole_count=4,
        shaft_diameter=6.0,
        shaft_length=5.0,
        center_bore_diameter=0,
        weight_g=55,
        voltage=5.0,
        current_a=1.5,
        torque_nm=0.1,
        step_angle=0,
    ),
}


def get_motor_spec(motor_name: str) -> MotorSpec | None:
    """获取电机规格。"""
    return MOTOR_SPECS.get(motor_name)


def list_motors(motor_type: str = "") -> list[dict[str, Any]]:
    """列出所有电机规格。

    Args:
        motor_type: 过滤类型 ("stepper", "dc", "servo")，空=全部

    Returns:
        电机规格列表
    """
    results = []
    for spec in MOTOR_SPECS.values():
        if motor_type and spec.motor_type != motor_type:
            continue
        results.append(spec.to_dict())
    return results


def recommend_coupling(shaft_diameter: float, motor_name: str = "") -> dict[str, Any]:
    """推荐联轴器参数。

    Args:
        shaft_diameter: 从动轴直径 (mm)
        motor_name: 电机名称（自动获取电机轴径）

    Returns:
        联轴器推荐参数
    """
    motor_shaft = 5.0
    if motor_name:
        spec = MOTOR_SPECS.get(motor_name)
        if spec:
            motor_shaft = spec.shaft_diameter

    # 联轴器规格
    bore_a = motor_shaft
    bore_b = shaft_diameter
    outer_d = max(bore_a, bore_b) * 2.5 + 5
    length = max(bore_a, bore_b) * 2 + 10

    return {
        "bore_a": bore_a,
        "bore_b": bore_b,
        "outer_diameter": round(outer_d, 1),
        "length": round(length, 1),
        "coupling_type": "jaw",  # 膜片联轴器
        "recommendation": f"轴径{motor_shaft}mm → {shaft_diameter}mm, 外径{outer_d:.0f}mm",
    }


def get_mount_params(motor_name: str) -> dict[str, Any]:
    """获取电机安装座参数。

    根据电机规格自动生成安装座设计参数。

    Args:
        motor_name: 电机名称

    Returns:
        安装座设计参数
    """
    spec = MOTOR_SPECS.get(motor_name)
    if not spec:
        return {"error": f"未知电机: {motor_name}"}

    pad = 10.0
    base_length = spec.body_size + pad * 2
    base_width = spec.body_size + pad
    hole_d = spec.mounting_hole_diameter + 0.5  # FDM 间隙

    return {
        "motor_name": motor_name,
        "base_length": round(base_length, 1),
        "base_width": round(base_width, 1),
        "mount_height": round(spec.body_length * 0.6, 1),
        "mounting_hole_spacing": spec.mounting_hole_spacing,
        "mounting_hole_diameter": round(hole_d, 1),
        "center_bore": round(spec.center_bore_diameter + 0.5, 1),
        "shaft_clearance_diameter": round(spec.shaft_diameter + 2.0, 1),
        "motor_hole_count": spec.mounting_hole_count,
        "base_hole_diameter": 5.5,  # M5 安装孔
    }
