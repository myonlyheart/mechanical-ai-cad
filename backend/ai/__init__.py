"""AI module - 自然语言 → 工程推理。"""

from .parser import IntentParser, DesignIntent
from .planner import EngineeringPlanner, EngineeringPlan
from .reasoning import ReasoningEngine, ReasoningResult


def generate_from_prompt(prompt: str) -> dict:
    """完整 AI 流程：用户输入 → 意图解析 → 工程规划 → 推理 → 输出。

    Args:
        prompt: 自然语言输入

    Returns:
        完整生成结果
    """
    parser = IntentParser()
    planner = EngineeringPlanner()
    reasoner = ReasoningEngine()

    # 1. 意图解析
    intent = parser.parse(prompt)

    # 2. 工程规划
    plan = planner.plan(intent)

    # 3. 工程推理
    result = reasoner.reason(intent, plan)

    return result.to_dict()


__all__ = [
    "IntentParser", "DesignIntent",
    "EngineeringPlanner", "EngineeringPlan",
    "ReasoningEngine", "ReasoningResult",
    "generate_from_prompt",
]
