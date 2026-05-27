"""Dirty Flag 增量更新系统。

核心原则：
- 修改参数后仅局部更新
- 禁止重新生成整个模型
- 通过依赖图追踪影响范围
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .dependency_graph import DependencyGraph


@dataclass
class DirtyNode:
    """脏标记节点。"""
    node_id: str = ""
    dirty: bool = False
    reason: str = ""
    priority: int = 0  # 优先级，数字越大越先更新


class DirtyFlagManager:
    """脏标记管理器 - 追踪需要更新的节点。

    工作流程：
    1. 参数修改 → 标记对应节点为 dirty
    2. 通过依赖图传播 dirty 标记
    3. 按拓扑序更新 dirty 节点
    """

    def __init__(self, graph: DependencyGraph | None = None) -> None:
        self._graph = graph or DependencyGraph()
        self._dirty_nodes: dict[str, DirtyNode] = {}
        self._update_callbacks: dict[str, Callable[[str, dict[str, Any]], Any]] = {}

    @property
    def graph(self) -> DependencyGraph:
        return self._graph

    def set_graph(self, graph: DependencyGraph) -> None:
        """设置依赖图。"""
        self._graph = graph

    def mark_dirty(self, node_id: str, reason: str = "", priority: int = 0) -> None:
        """标记节点为 dirty，并传播到所有依赖节点。"""
        self._dirty_nodes[node_id] = DirtyNode(
            node_id=node_id, dirty=True, reason=reason, priority=priority,
        )

        # 传播到所有依赖此节点的节点
        dependents = self._graph.get_all_dependents(node_id)
        for dep_id in dependents:
            if dep_id not in self._dirty_nodes:
                self._dirty_nodes[dep_id] = DirtyNode(
                    node_id=dep_id, dirty=True,
                    reason=f"propagated from {node_id}",
                )

    def mark_clean(self, node_id: str) -> None:
        """标记节点为 clean。"""
        self._dirty_nodes.pop(node_id, None)

    def is_dirty(self, node_id: str) -> bool:
        """检查节点是否 dirty。"""
        return node_id in self._dirty_nodes

    def get_dirty_nodes(self) -> list[DirtyNode]:
        """获取所有 dirty 节点，按优先级排序。"""
        return sorted(
            self._dirty_nodes.values(),
            key=lambda n: (-n.priority, n.node_id),
        )

    def get_dirty_count(self) -> int:
        """获取 dirty 节点数量。"""
        return len(self._dirty_nodes)

    def clear_all(self) -> None:
        """清除所有 dirty 标记。"""
        self._dirty_nodes.clear()

    def register_callback(
        self, node_id: str, callback: Callable[[str, dict[str, Any]], Any]
    ) -> None:
        """注册节点更新回调。"""
        self._update_callbacks[node_id] = callback

    def update_dirty(self) -> list[dict[str, Any]]:
        """按拓扑序更新所有 dirty 节点。

        Returns:
            每个节点的更新结果列表
        """
        results: list[dict[str, Any]] = []
        dirty_ids = set(self._dirty_nodes.keys())

        try:
            order = self._graph.get_topological_order()
        except ValueError:
            # 有环时直接按现有顺序
            order = list(dirty_ids)

        for node_id in order:
            if node_id not in dirty_ids:
                continue

            node_info = self._graph._nodes.get(node_id)
            result = {
                "node_id": node_id,
                "name": node_info.name if node_info else node_id,
                "updated": False,
                "error": None,
            }

            # 执行回调
            callback = self._update_callbacks.get(node_id)
            if callback:
                try:
                    callback(node_id, node_info.data if node_info else {})
                    result["updated"] = True
                except Exception as e:
                    result["error"] = str(e)

            self.mark_clean(node_id)
            results.append(result)

        return results

    def to_dict(self) -> dict[str, Any]:
        """序列化。"""
        return {
            "dirty_count": len(self._dirty_nodes),
            "dirty_nodes": [
                {"node_id": n.node_id, "reason": n.reason, "priority": n.priority}
                for n in self._dirty_nodes.values()
            ],
        }
