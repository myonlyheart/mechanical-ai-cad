"""Assembly Tree - 父子层级结构 + Transform 传播。

核心原则：
- geometry 与 transform 分离
- 禁止直接修改原始几何
- 父变换向下传播到子节点
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from ...core.models import Part


@dataclass
class Transform3D:
    """3D 变换矩阵（简化表示）。

    使用 position + rotation（四元数）+ scale 表示。
    四元数格式: (x, y, z, w)
    """
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)  # (x, y, z, w)
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)

    def apply_to_point(self, point: tuple[float, float, float]) -> tuple[float, float, float]:
        """将变换应用到一个点：先缩放，再旋转，最后平移。"""
        # 1. 缩放
        sx = point[0] * self.scale[0]
        sy = point[1] * self.scale[1]
        sz = point[2] * self.scale[2]

        # 2. 四元数旋转: v' = q * v * q^-1
        rx, ry, rz, rw = self.rotation
        # 优化公式（避免完整四元数乘法）
        # v' = v + 2 * q_xyz × (q_xyz × v + q_w * v)
        tx = 2.0 * (ry * sz - rz * sy)
        ty = 2.0 * (rz * sx - rx * sz)
        tz = 2.0 * (rx * sy - ry * sx)
        rx_out = sx + rw * tx + (ry * tz - rz * ty)
        ry_out = sy + rw * ty + (rz * tx - rx * tz)
        rz_out = sz + rw * tz + (rx * ty - ry * tx)

        # 3. 平移
        return (
            rx_out + self.position[0],
            ry_out + self.position[1],
            rz_out + self.position[2],
        )

    def multiply(self, other: Transform3D) -> Transform3D:
        """组合两个变换：self * other（先应用 other，再应用 self）。

        位置: p = self.pos + self.rot * (self.scale * other.pos)
        旋转: q = self.rot * other.rot
        缩放: s = self.scale * other.scale
        """
        # 四元数乘法: q1 * q2
        ax, ay, az, aw = self.rotation
        bx, by, bz, bw = other.rotation
        new_rw = aw * bw - ax * bx - ay * by - az * bz
        new_rx = aw * bx + ax * bw + ay * bz - az * by
        new_ry = aw * by - ax * bz + ay * bw + az * bx
        new_rz = aw * bz + ax * by - ay * bx + az * bw

        # 缩放 other 的位置
        ox = other.position[0] * self.scale[0]
        oy = other.position[1] * self.scale[1]
        oz = other.position[2] * self.scale[2]

        # 用 self.rotation 旋转缩放后的位置
        tx = 2.0 * (ay * oz - az * oy)
        ty = 2.0 * (az * ox - ax * oz)
        tz = 2.0 * (ax * oy - ay * ox)
        rx_out = ox + aw * tx + (ay * tz - az * ty)
        ry_out = oy + aw * ty + (az * tx - ax * tz)
        rz_out = oz + aw * tz + (ax * ty - ay * tx)

        return Transform3D(
            position=(
                self.position[0] + rx_out,
                self.position[1] + ry_out,
                self.position[2] + rz_out,
            ),
            rotation=(new_rx, new_ry, new_rz, new_rw),
            scale=(
                self.scale[0] * other.scale[0],
                self.scale[1] * other.scale[1],
                self.scale[2] * other.scale[2],
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
        }

    @classmethod
    def identity(cls) -> Transform3D:
        return cls()

    @classmethod
    def from_position(cls, x: float, y: float, z: float) -> Transform3D:
        return cls(position=(x, y, z))

    @classmethod
    def from_rotation(cls, rx: float, ry: float, rz: float) -> Transform3D:
        """从欧拉角（弧度）创建旋转变换。"""
        import math
        # 欧拉角 → 四元数 (ZYX 顺序)
        cx, sx = math.cos(rx / 2), math.sin(rx / 2)
        cy, sy = math.cos(ry / 2), math.sin(ry / 2)
        cz, sz = math.cos(rz / 2), math.sin(rz / 2)
        w = cx * cy * cz + sx * sy * sz
        x = sx * cy * cz - cx * sy * sz
        y = cx * sy * cz + sx * cy * sz
        z = cx * cy * sz - sx * sy * cz
        return cls(rotation=(x, y, z, w))


@dataclass
class AssemblyNode:
    """装配树节点 - 表示装配层级中的一个节点。

    每个节点有：
    - local_transform: 相对于父节点的变换
    - parent 引用
    - children 子节点列表
    - part: 关联的零件（叶子节点）

    Transform 传播：
    - world_transform = parent.world_transform * local_transform
    - geometry 不被修改，变换在渲染时计算
    """
    id: str = ""
    name: str = ""
    local_transform: Transform3D = field(default_factory=Transform3D)
    part: Optional[Part] = None
    parent: Optional[AssemblyNode] = None
    children: list[AssemblyNode] = field(default_factory=list)
    visible: bool = True
    locked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    @property
    def world_transform(self) -> Transform3D:
        """计算世界变换 = 父变换 × 本地变换。"""
        if self.parent is None:
            return self.local_transform
        return self.parent.world_transform.multiply(self.local_transform)

    def add_child(self, node: AssemblyNode) -> None:
        """添加子节点。"""
        node.parent = self
        self.children.append(node)

    def remove_child(self, node_id: str) -> Optional[AssemblyNode]:
        """移除子节点。"""
        for i, child in enumerate(self.children):
            if child.id == node_id:
                child.parent = None
                return self.children.pop(i)
        return None

    def find_node(self, name: str) -> Optional[AssemblyNode]:
        """按名称查找节点（递归）。"""
        if self.name == name:
            return self
        for child in self.children:
            result = child.find_node(name)
            if result:
                return result
        return None

    def get_all_parts(self) -> list[tuple[str, Part, Transform3D]]:
        """获取所有叶子节点的零件及其世界变换。"""
        parts: list[tuple[str, Part, Transform3D]] = []
        self._collect_parts(parts)
        return parts

    def _collect_parts(self, parts: list[tuple[str, Part, Transform3D]]) -> None:
        """递归收集零件。"""
        if self.part is not None:
            parts.append((self.name, self.part, self.world_transform))
        for child in self.children:
            child._collect_parts(parts)

    def get_depth(self) -> int:
        """获取节点深度。"""
        depth = 0
        node = self
        while node.parent is not None:
            depth += 1
            node = node.parent
        return depth

    def is_leaf(self) -> bool:
        """是否为叶子节点。"""
        return len(self.children) == 0

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典。"""
        return {
            "id": self.id,
            "name": self.name,
            "local_transform": self.local_transform.to_dict(),
            "world_transform": self.world_transform.to_dict(),
            "part": self.part.to_dict() if self.part else None,
            "visible": self.visible,
            "locked": self.locked,
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata,
        }


class AssemblyTree:
    """装配树 - 管理整个装配层级。

    示例:
        Robot (root)
         ├── Base
         ├── Motor
         └── Arm
    """

    def __init__(self, name: str = "assembly") -> None:
        self.root = AssemblyNode(name=name)
        self._node_cache: dict[str, AssemblyNode] = {}

    def add_part(
        self,
        part: Part,
        parent_name: str = "",
        local_position: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> AssemblyNode:
        """添加零件到装配树。

        Args:
            part: 零件对象
            parent_name: 父节点名称（空则挂在 root 下）
            local_position: 相对父节点的位置

        Returns:
            创建的节点
        """
        node = AssemblyNode(
            name=part.name,
            part=part,
            local_transform=Transform3D.from_position(*local_position),
        )

        if parent_name:
            parent = self.root.find_node(parent_name)
            if parent is None:
                raise ValueError(f"未找到父节点: {parent_name}")
            parent.add_child(node)
        else:
            self.root.add_child(node)

        self._node_cache[node.name] = node
        return node

    def add_subassembly(
        self,
        name: str,
        parent_name: str = "",
        local_position: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> AssemblyNode:
        """添加子装配节点（无零件，仅分组）。"""
        node = AssemblyNode(
            name=name,
            local_transform=Transform3D.from_position(*local_position),
        )

        if parent_name:
            parent = self.root.find_node(parent_name)
            if parent is None:
                raise ValueError(f"未找到父节点: {parent_name}")
            parent.add_child(node)
        else:
            self.root.add_child(node)

        self._node_cache[node.name] = node
        return node

    def find(self, name: str) -> Optional[AssemblyNode]:
        """查找节点。"""
        return self._node_cache.get(name) or self.root.find_node(name)

    def get_all_parts(self) -> list[tuple[str, Part, Transform3D]]:
        """获取所有零件及其世界变换。"""
        return self.root.get_all_parts()

    def flat_list(self) -> list[dict[str, Any]]:
        """获取所有节点的扁平列表（用于 Three.js 渲染）。"""
        result: list[dict[str, Any]] = []
        self._flat_list(self.root, result, depth=0)
        return result

    def _flat_list(
        self, node: AssemblyNode, result: list[dict[str, Any]], depth: int
    ) -> None:
        if node != self.root:
            result.append({
                "id": node.id,
                "name": node.name,
                "depth": depth,
                "has_part": node.part is not None,
                "visible": node.visible,
                "locked": node.locked,
                "world_position": node.world_transform.position,
            })
        for child in node.children:
            self._flat_list(child, result, depth + 1)

    def to_dict(self) -> dict[str, Any]:
        """序列化。"""
        return self.root.to_dict()
