"""对齐求解器 - 计算零件间的对齐变换矩阵"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AlignmentRule:
    """对齐规则定义"""
    type: str            # "hole_to_hole" | "shaft_center" | "face_to_face" | "z_axis"
    part_a: str          # 零件 A 名称
    part_b: str          # 零件 B 名称
    feature_a: str       # A 上的特征（孔名 / 轴名 / 面名）
    feature_b: str       # B 上的特征
    clearance: float = 0.2  # 间隙（mm）


# 标准装配规则模板
ASSEMBLY_RULES_TEMPLATES = {
    ("motor", "bracket"): [
        AlignmentRule("hole_to_hole", "motor", "bracket", "mounting_holes", "mounting_holes"),
        AlignmentRule("z_axis", "motor", "bracket", "shaft", "center_bore"),
    ],
    ("motor", "motor_mount"): [
        AlignmentRule("hole_to_hole", "motor", "motor_mount", "mounting_holes", "mounting_holes"),
        AlignmentRule("shaft_center", "motor", "motor_mount", "shaft", "center_bore"),
    ],
    ("shaft", "bearing"): [
        AlignmentRule("shaft_center", "shaft", "bearing", "shaft_body", "inner_race"),
    ],
    ("bearing", "bracket"): [
        AlignmentRule("hole_to_hole", "bearing", "bracket", "outer_race", "housing_bore"),
    ],
    ("gear", "shaft"): [
        AlignmentRule("shaft_center", "gear", "shaft", "bore", "shaft_body"),
    ],
}


def get_alignment_rules(part_a: str, part_b: str) -> list[AlignmentRule]:
    """获取两个零件之间的对齐规则"""
    key = (part_a, part_b)
    reverse_key = (part_b, part_a)

    rules = ASSEMBLY_RULES_TEMPLATES.get(key, [])
    if not rules:
        rules = ASSEMBLY_RULES_TEMPLATES.get(reverse_key, [])

    return rules


def compute_hole_alignment(pos_a: tuple, pos_b: tuple, clearance: float) -> dict:
    """计算孔对孔的对齐变换

    Args:
        pos_a: 零件 A 孔的中心位置 (x, y, z)
        pos_b: 零件 B 孔的中心位置 (x, y, z)
        clearance: 间隙（mm）

    Returns:
        变换矩阵描述
    """
    dx = pos_b[0] - pos_a[0]
    dy = pos_b[1] - pos_a[1]
    dz = pos_b[2] - pos_a[2]

    return {
        "type": "translate",
        "x": dx,
        "y": dy,
        "z": dz + clearance,
    }


def compute_shaft_center_alignment(center_a: tuple, center_b: tuple) -> dict:
    """计算轴心对齐变换"""
    dx = center_b[0] - center_a[0]
    dy = center_b[1] - center_a[1]
    dz = center_b[2] - center_a[2]

    return {
        "type": "translate",
        "x": dx,
        "y": dy,
        "z": dz,
    }


def solve_alignment(parts: list[dict], rules: list[AlignmentRule]) -> list[dict]:
    """求解所有对齐规则，生成变换矩阵列表

    Args:
        parts: 零件列表 [{"name": "motor", "position": (0,0,0), "features": {...}}, ...]
        rules: 对齐规则列表

    Returns:
        变换矩阵列表
    """
    transforms = []
    part_positions = {p["name"]: p.get("position", (0, 0, 0)) for p in parts}
    part_features = {p["name"]: p.get("features", {}) for p in parts}

    for rule in rules:
        pos_a = part_positions.get(rule.part_a, (0, 0, 0))
        pos_b = part_positions.get(rule.part_b, (0, 0, 0))

        if rule.type == "hole_to_hole":
            transform = compute_hole_alignment(pos_a, pos_b, rule.clearance)
        elif rule.type in ("shaft_center", "z_axis"):
            transform = compute_shaft_center_alignment(pos_a, pos_b)
        else:
            transform = compute_shaft_center_alignment(pos_a, pos_b)

        transform["rule"] = f"{rule.part_a}.{rule.feature_a} → {rule.part_b}.{rule.feature_b}"
        transform["part"] = rule.part_b  # 移动零件 B
        transforms.append(transform)

    return transforms
