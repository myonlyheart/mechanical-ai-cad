"""AI Reasoning Engine - 工程推理。

流程：工程方案 → 约束验证 → 方案评分 → 推荐
这是 AI 流程的第三步，对工程方案进行推理、验证和评分。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..parser.intent import DesignIntent
from ..planner.engine import EngineeringPlan
from ...constraint_engine import check_and_fix
from ...engineering.optimization.variants import (
    generate_variants, compare_variants, recommend_variant, score_variant,
)


@dataclass
class ReasoningResult:
    """推理结果。"""
    intent: dict[str, Any] = field(default_factory=dict)
    plan: dict[str, Any] = field(default_factory=dict)
    variants: list[dict[str, Any]] = field(default_factory=list)
    comparison: list[dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    reasoning_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "plan": self.plan,
            "variants": self.variants,
            "comparison": self.comparison,
            "recommendation": self.recommendation,
            "reasoning_steps": self.reasoning_steps,
        }


class ReasoningEngine:
    """工程推理引擎 - 验证、评分、推荐。"""

    def reason(self, intent: DesignIntent, plan: EngineeringPlan) -> ReasoningResult:
        """执行工程推理。

        Args:
            intent: 设计意图
            plan: 工程方案

        Returns:
            ReasoningResult
        """
        steps: list[str] = []

        # Step 1: 生成变体
        steps.append(f"生成 {len(plan.designs)} 个设计方案")
        variants = generate_variants(
            plan.part_type,
            plan.base_params,
            plan.designs,
            plan.optimization_goal,
        )
        steps.append(f"完成约束检查和评分，共 {len(variants)} 个变体")

        # Step 2: 对比
        comparison = compare_variants(variants)
        steps.append("生成方案对比表")

        # Step 3: 推荐
        recommendation = recommend_variant(variants)
        if recommendation:
            top = next((v for v in variants if v["design_id"] == recommendation), None)
            if top:
                steps.append(f"推荐方案: {top['name']} (评分: {top['scores']['total']})")

        return ReasoningResult(
            intent=intent.to_dict(),
            plan=plan.to_dict(),
            variants=variants,
            comparison=comparison,
            recommendation=recommendation,
            reasoning_steps=steps,
        )

    def reason_single(
        self, part_type: str, params: dict[str, Any],
    ) -> dict[str, Any]:
        """对单组参数执行约束检查和推理。

        Args:
            part_type: 零件类型
            params: 参数

        Returns:
            检查结果 + 评分
        """
        check_result = check_and_fix(part_type, params)
        scores = score_variant(check_result["fixed_params"])

        return {
            "constraint_check": check_result,
            "scores": scores,
        }
