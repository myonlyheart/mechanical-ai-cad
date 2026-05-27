"""统一工程数据结构 - 所有模块必须使用此结构传递数据。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Anchor:
    """装配锚点 - 定义零件上的可连接位置。

    Attributes:
        id: 唯一标识符
        name: 锚点名称（如 mount_face, shaft_axis）
        type: 锚点类型 (point | face | edge | axis | hole_center)
        position: 世界坐标位置 (x, y, z) mm
        direction: 方向向量 (dx, dy, dz)
        metadata: 附加信息（孔径、间距等）
    """
    id: str = ""
    name: str = ""
    type: str = "point"  # point | face | edge | axis | hole_center
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    direction: tuple[float, float, float] = (0.0, 0.0, 1.0)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class Part:
    """工程零件 - 统一数据结构。

    所有模块只能读取此结构，禁止自由 JSON 混乱传递。

    Attributes:
        id: 唯一标识符
        name: 零件名称
        part_type: 零件类型 (bracket | gear | motor_mount | ...)
        parameters: 参数字典
        geometry: build123d 几何对象（可为 None）
        anchors: 锚点列表
        metadata: 附加元数据（材料、质量等）
    """
    id: str = ""
    name: str = ""
    part_type: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    geometry: Any = None
    anchors: list[Anchor] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def get_anchor(self, name: str) -> Optional[Anchor]:
        """按名称查找锚点。"""
        for a in self.anchors:
            if a.name == name:
                return a
        return None

    def get_anchors_by_type(self, anchor_type: str) -> list[Anchor]:
        """按类型筛选锚点。"""
        return [a for a in self.anchors if a.type == anchor_type]

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典（不含 geometry）。"""
        return {
            "id": self.id,
            "name": self.name,
            "part_type": self.part_type,
            "parameters": self.parameters,
            "anchors": [
                {
                    "id": a.id, "name": a.name, "type": a.type,
                    "position": a.position, "direction": a.direction,
                    "metadata": a.metadata,
                }
                for a in self.anchors
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Part:
        """从字典反序列化（无 geometry）。"""
        anchors = [
            Anchor(
                id=a.get("id", ""), name=a.get("name", ""),
                type=a.get("type", "point"),
                position=tuple(a.get("position", (0, 0, 0))),
                direction=tuple(a.get("direction", (0, 0, 1))),
                metadata=a.get("metadata", {}),
            )
            for a in data.get("anchors", [])
        ]
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            part_type=data.get("part_type", ""),
            parameters=data.get("parameters", {}),
            anchors=anchors,
            metadata=data.get("metadata", {}),
        )


@dataclass
class Assembly:
    """装配体 - 包含多个零件及其约束关系。

    Attributes:
        id: 唯一标识符
        name: 装配体名称
        children: 子零件列表
        constraints: 约束列表
        metadata: 附加元数据
    """
    id: str = ""
    name: str = ""
    children: list[Part] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def add_part(self, part: Part) -> None:
        """添加零件到装配体。"""
        self.children.append(part)

    def get_part(self, name: str) -> Optional[Part]:
        """按名称查找零件。"""
        for p in self.children:
            if p.name == name:
                return p
        return None

    def add_constraint(self, constraint: dict[str, Any]) -> None:
        """添加约束。"""
        self.constraints.append(constraint)

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典。"""
        return {
            "id": self.id,
            "name": self.name,
            "children": [p.to_dict() for p in self.children],
            "constraints": self.constraints,
            "metadata": {
                **self.metadata,
                "part_count": len(self.children),
                "constraint_count": len(self.constraints),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Assembly:
        """从字典反序列化。"""
        children = [Part.from_dict(p) for p in data.get("children", [])]
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            children=children,
            constraints=data.get("constraints", []),
            metadata=data.get("metadata", {}),
        )
