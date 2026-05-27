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
    """
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)  # (x, y, z, w)
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)

    def apply_to_point(self, point: tuple[float, float, float]) -> tuple[float, float, float]:
        """将变换应用到一个点（简化：仅平移）。"""
        return (
            point[0] + self.position[0],
            point[1] + self.position[1],
            point[2] + self.position[2],
        )

    def multiply(self, other: Transform3D) -> Transform3D:
        """组合两个变换（简化：仅组合平移）。"""
        return Transform3D(
            position=(
                self.position[0] + other.position[0],
                self.position[1] + other.position[1],
                self.position[2] + other.position[2],
            ),
            rotation=self.rotation,
            scale=self.scale,
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
