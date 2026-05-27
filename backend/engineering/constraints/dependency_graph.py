"""依赖图 - 管理参数、约束、装配之间的依赖关系。

支持：
- 参数依赖（修改参数 A 影响参数 B）
- 约束依赖（约束 A 依赖约束 B 的结果）
- Assembly 依赖（零件 A 的位置依赖零件 B）
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class NodeType(str, Enum):
    """依赖节点类型。"""
    PARAMETER = "parameter"
    CONSTRAINT = "constraint"
    PART = "part"
    ASSEMBLY = "assembly"


@dataclass
class DependencyNode:
    """依赖图节点。"""
    id: str = ""
    name: str = ""
    type: str = NodeType.PARAMETER
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class DependencyEdge:
    """依赖边：source → target 表示 target 依赖 source。"""
    source: str = ""
    target: str = ""
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise ValueError("Edge requires both source and target")


class DependencyGraph:
    """依赖图 - 有向无环图（DAG）。

    用于追踪参数修改的影响范围，支持增量更新。
    """

    def __init__(self) -> None:
        self._nodes: dict[str, DependencyNode] = {}
        self._edges: list[DependencyEdge] = []
        self._adj: dict[str, list[str]] = defaultdict(list)       # source → [targets]
        self._reverse: dict[str, list[str]] = defaultdict(list)   # target → [sources]

    def add_node(
        self, name: str, node_type: str = NodeType.PARAMETER,
        data: dict[str, Any] | None = None,
    ) -> str:
        """添加节点，返回节点 ID。"""
        node = DependencyNode(name=name, type=node_type, data=data or {})
        self._nodes[node.id] = node
        return node.id

    def add_edge(self, source_id: str, target_id: str, weight: float = 1.0) -> None:
        """添加依赖边（source → target）。"""
        if source_id not in self._nodes or target_id not in self._nodes:
            raise ValueError("Both nodes must exist before adding edge")
        edge = DependencyEdge(source=source_id, target=target_id, weight=weight)
        self._edges.append(edge)
        self._adj[source_id].append(target_id)
        self._reverse[target_id].append(source_id)

    def get_dependents(self, node_id: str) -> list[str]:
        """获取直接依赖此节点的所有节点。"""
        return list(self._adj.get(node_id, []))

    def get_dependencies(self, node_id: str) -> list[str]:
        """获取此节点直接依赖的所有节点。"""
        return list(self._reverse.get(node_id, []))

    def get_all_dependents(self, node_id: str) -> set[str]:
        """获取所有传递依赖此节点的节点（BFS）。"""
        visited: set[str] = set()
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            for dep in self._adj.get(current, []):
                if dep not in visited:
                    visited.add(dep)
                    queue.append(dep)
        return visited

    def get_topological_order(self) -> list[str]:
        """获取拓扑排序。"""
        in_degree: dict[str, int] = {nid: 0 for nid in self._nodes}
        for edge in self._edges:
            in_degree[edge.target] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for target in self._adj.get(node, []):
                in_degree[target] -= 1
                if in_degree[target] == 0:
                    queue.append(target)

        if len(order) != len(self._nodes):
            raise ValueError("Dependency graph has cycles")

        return order

    def has_cycle(self) -> bool:
        """检测是否存在环。"""
        try:
            self.get_topological_order()
            return False
        except ValueError:
            return True

    def find_node_by_name(self, name: str) -> Optional[str]:
        """按名称查找节点 ID。"""
        for nid, node in self._nodes.items():
            if node.name == name:
                return nid
        return None

    def get_affected_nodes(self, changed_node_id: str) -> list[dict[str, Any]]:
        """获取修改某节点后受影响的所有节点（按拓扑序）。"""
        affected_ids = self.get_all_dependents(changed_node_id)
        try:
            order = self.get_topological_order()
        except ValueError:
            order = list(affected_ids)

        result = []
        for nid in order:
            if nid in affected_ids:
                node = self._nodes[nid]
                result.append({
                    "id": nid, "name": node.name, "type": node.type,
                    "data": node.data,
                })
        return result

    def to_dict(self) -> dict[str, Any]:
        """序列化。"""
        return {
            "nodes": [
                {"id": n.id, "name": n.name, "type": n.type, "data": n.data}
                for n in self._nodes.values()
            ],
            "edges": [
                {"source": e.source, "target": e.target, "weight": e.weight}
                for e in self._edges
            ],
        }
