"""碰撞检测 - 检查装配体中零件之间的碰撞。

支持：
- AABB（轴对齐包围盒）
- Bounding Box 碰撞检测
- 检测穿模、螺丝冲突、零件重叠
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

from ...core.models import Part


@dataclass
class AABB:
    """轴对齐包围盒。"""
    min_x: float = 0.0
    min_y: float = 0.0
    min_z: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0
    max_z: float = 0.0

    @property
    def center(self) -> tuple[float, float, float]:
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2,
        )

    @property
    def size(self) -> tuple[float, float, float]:
        return (
            self.max_x - self.min_x,
            self.max_y - self.min_y,
            self.max_z - self.min_z,
        )

    def intersects(self, other: AABB) -> bool:
        """检查两个 AABB 是否相交。"""
        return (
            self.min_x <= other.max_x and self.max_x >= other.min_x
            and self.min_y <= other.max_y and self.max_y >= other.min_y
            and self.min_z <= other.max_z and self.max_z >= other.min_z
        )

    def intersection_volume(self, other: AABB) -> float:
        """计算相交体积。"""
        dx = min(self.max_x, other.max_x) - max(self.min_x, other.min_x)
        dy = min(self.max_y, other.max_y) - max(self.min_y, other.min_y)
        dz = min(self.max_z, other.max_z) - max(self.min_z, other.min_z)
        if dx <= 0 or dy <= 0 or dz <= 0:
            return 0.0
        return dx * dy * dz

    def to_dict(self) -> dict[str, Any]:
        return {
            "min": (self.min_x, self.min_y, self.min_z),
            "max": (self.max_x, self.max_y, self.max_z),
            "center": self.center,
            "size": self.size,
        }


@dataclass
class CollisionResult:
    """碰撞检测结果。"""
    part_a: str = ""
    part_b: str = ""
    colliding: bool = False
    overlap_volume: float = 0.0
    severity: str = "error"  # error | warning
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "part_a": self.part_a,
            "part_b": self.part_b,
            "colliding": self.colliding,
            "overlap_volume": self.overlap_volume,
            "severity": self.severity,
            "message": self.message,
        }


def compute_aabb(geometry: Any, position: tuple[float, float, float] = (0, 0, 0)) -> Optional[AABB]:
    """从几何对象计算 AABB。

    Args:
        geometry: build123d 几何对象
        position: 几何体的位置偏移

    Returns:
        AABB 或 None
    """
    if geometry is None:
        return None

    try:
        if hasattr(geometry, "bounding_box"):
            bb = geometry.bounding_box()
            return AABB(
                min_x=bb.min.X + position[0],
                min_y=bb.min.Y + position[1],
                min_z=bb.min.Z + position[2],
                max_x=bb.max.X + position[0],
                max_y=bb.max.Y + position[1],
                max_z=bb.max.Z + position[2],
            )
    except Exception:
        pass

    return None


def check_collision_pair(
    name_a: str, aabb_a: AABB,
    name_b: str, aabb_b: AABB,
    tolerance: float = 0.1,
) -> CollisionResult:
    """检查两个零件的碰撞。"""
    if not aabb_a.intersects(aabb_b):
        return CollisionResult(
            part_a=name_a, part_b=name_b,
            colliding=False, message="无碰撞",
        )

    volume = aabb_a.intersection_volume(aabb_b)
    severity = "error" if volume > tolerance * 10 else "warning"

    return CollisionResult(
        part_a=name_a, part_b=name_b,
        colliding=True,
        overlap_volume=volume,
        severity=severity,
        message=f"碰撞: {name_a} 和 {name_b} 重叠 {volume:.2f}mm³",
    )


def check_assembly_collisions(
    parts_with_aabbs: list[tuple[str, AABB]],
    tolerance: float = 0.1,
) -> dict[str, Any]:
    """检查装配体中所有零件对的碰撞。

    Args:
        parts_with_aabbs: [(part_name, AABB), ...]
        tolerance: 碰撞容差

    Returns:
        {"valid": bool, "collisions": [...]}
    """
    collisions: list[dict[str, Any]] = []

    for i in range(len(parts_with_aabbs)):
        for j in range(i + 1, len(parts_with_aabbs)):
            name_a, aabb_a = parts_with_aabbs[i]
            name_b, aabb_b = parts_with_aabbs[j]
            result = check_collision_pair(name_a, aabb_a, name_b, aabb_b, tolerance)
            if result.colliding:
                collisions.append(result.to_dict())

    has_error = any(c["severity"] == "error" for c in collisions)

    return {
        "valid": not has_error,
        "collision_count": len(collisions),
        "collisions": collisions,
    }


def check_hole_overlap(
    parts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """检查螺丝孔是否重叠（同位置多个孔导致冲突）。"""
    overlaps: list[dict[str, Any]] = []

    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            anchors_i = parts[i].get("anchors", [])
            anchors_j = parts[j].get("anchors", [])

            for a in anchors_i:
                if a.get("type") != "hole_center":
                    continue
                for b in anchors_j:
                    if b.get("type") != "hole_center":
                        continue

                    pos_a = a.get("position", (0, 0, 0))
                    pos_b = b.get("position", (0, 0, 0))
                    dist = math.sqrt(
                        (pos_a[0] - pos_b[0]) ** 2
                        + (pos_a[1] - pos_b[1]) ** 2
                        + (pos_a[2] - pos_b[2]) ** 2
                    )

                    dia_a = a.get("metadata", {}).get("diameter", 5)
                    dia_b = b.get("metadata", {}).get("diameter", 5)

                    if dist < (dia_a + dia_b) / 2:
                        overlaps.append({
                            "part_a": parts[i].get("name", ""),
                            "part_b": parts[j].get("name", ""),
                            "hole_a": a.get("name", ""),
                            "hole_b": b.get("name", ""),
                            "distance": round(dist, 2),
                            "message": f"孔重叠: {parts[i].get('name')}.{a.get('name')} 和 {parts[j].get('name')}.{b.get('name')}",
                        })

    return overlaps
