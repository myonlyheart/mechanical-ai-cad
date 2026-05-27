"""Engineering Planner - 工程规划器。

流程：设计意图 → 工程方案 → 约束规划 → 参数化方案列表
这是 AI 流程的第二步，将设计意图转为可执行的工程方案。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..parser.intent import DesignIntent
from ...design_generator.planner import plan_designs


@dataclass
class EngineeringPlan:
    """工程规划结果。"""
    part_type: str = ""
    base_params: dict[str, Any] = field(default_factory=dict)
    designs: list[dict[str, Any]] = field(default_factory=list)
    optimization_goal: str = "balanced"
    constraints_to_apply: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "part_type": self.part_type,
            "base_params": self.base_params,
            "designs": self.designs,
            "optimization_goal": self.optimization_goal,
            "constraints_to_apply": self.constraints_to_apply,
        }


class EngineeringPlanner:
    """工程规划器 - 将设计意图转为工程方案。"""

    def plan(self, intent: DesignIntent) -> EngineeringPlan:
        """根据设计意图生成工程方案。

        Args:
            intent: 设计意图

        Returns:
            EngineeringPlan
        """
        # 确定优化目标
        goal = self._determine_goal(intent.priority)

        # 生成设计方案
        designs = plan_designs(intent.object, intent.requirements)

        # 确定需要应用的约束
        constraints = self._plan_constraints(intent)

        return EngineeringPlan(
            part_type=intent.object,
            base_params=intent.base_params,
            designs=designs,
            optimization_goal=goal,
            constraints_to_apply=constraints,
            metadata={
                "original_prompt": intent.original_prompt,
                "priorities": intent.priority,
                "assembly_intent": intent.assembly_intent,
            },
        )

    def _determine_goal(self, priorities: list[str]) -> str:
        """根据优先级确定优化目标。"""
        if not priorities:
            return "balanced"
        top = priorities[0]
        goal_map = {
            "lightweight": "lightweight",
            "rigid": "high_strength",
            "fast_print": "easy_print",
            "low_cost": "low_cost",
            "printable": "easy_print",
        }
        return goal_map.get(top, "balanced")

    def _plan_constraints(self, intent: DesignIntent) -> list[str]:
        """规划需要应用的约束。"""
        constraints: list[str] = []

        # 基础制造约束（始终应用）
        constraints.append("manufacturing_check")
        constraints.append("geometry_check")

        # 标准件约束
        if intent.constraints.get("screw"):
            constraints.append("screw_standard_check")
        if intent.constraints.get("motor_type"):
            constraints.append("nema_standard_check")
        if intent.constraints.get("bearing"):
            constraints.append("bearing_standard_check")

        # 装配约束
        if intent.assembly_intent:
            constraints.append("assembly_collision_check")

        # 设计约束
        for ci in intent.constraint_intent:
            constraints.append(f"design_{ci}")

        return constraints
