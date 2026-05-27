"""Intent Parser - 自然语言意图解析。

流程：用户输入 → 意图识别 → 实体提取 → 约束提取 → 结构化 DSL
这是 AI 流程的第一步，将非结构化文本转为结构化设计意图。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ...prompts.prompt_engine import PromptEngine


# ============================================================
# 关键词映射表
# ============================================================

LOAD_KEYWORDS = {
    "轻量": "light", "轻": "light", "lightweight": "light", "小型": "light",
    "中等": "medium", "普通": "medium", "标准": "medium",
    "重型": "heavy", "重载": "heavy", "高强度": "heavy", "heavy duty": "heavy",
}

MATERIAL_KEYWORDS = {
    "pla": "PLA", "abs": "ABS", "petg": "PETG", "tpu": "TPU", "nylon": "Nylon",
    "尼龙": "Nylon", "柔性": "TPU", "橡胶": "TPU",
}

PRIORITY_KEYWORDS = {
    "轻量": "lightweight", "轻": "lightweight", "减重": "lightweight",
    "强度": "rigid", "结实": "rigid", "刚性": "rigid", "坚固": "rigid",
    "打印": "printable", "可制造": "printable", "快速": "fast_print",
    "便宜": "low_cost", "成本": "low_cost",
}

ASSEMBLY_KEYWORDS = {
    "安装": "assemble", "装配": "assemble", "组装": "assemble",
    "固定": "fix", "连接": "connect", "配合": "mate",
    "螺栓": "bolt", "螺丝": "screw",
}

CONSTRAINT_KEYWORDS = {
    "对称": "symmetric", "居中": "centered", "对齐": "aligned",
    "平行": "parallel", "垂直": "perpendicular",
}


@dataclass
class DesignIntent:
    """设计意图 DSL。"""
    object: str = ""               # 零件类型
    constraints: dict[str, Any] = field(default_factory=dict)
    priority: list[str] = field(default_factory=list)
    base_params: dict[str, Any] = field(default_factory=dict)
    requirements: dict[str, Any] = field(default_factory=dict)
    assembly_intent: list[str] = field(default_factory=list)
    constraint_intent: list[str] = field(default_factory=list)
    original_prompt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "object": self.object,
            "constraints": self.constraints,
            "priority": self.priority,
            "base_params": self.base_params,
            "requirements": self.requirements,
            "assembly_intent": self.assembly_intent,
            "constraint_intent": self.constraint_intent,
            "original_prompt": self.original_prompt,
        }


class IntentParser:
    """意图解析器 - 将自然语言转为结构化设计意图。"""

    def __init__(self) -> None:
        self._engine = PromptEngine()

    def parse(self, prompt: str) -> DesignIntent:
        """解析用户输入。

        Args:
            prompt: 用户自然语言输入

        Returns:
            DesignIntent
        """
        lower = prompt.lower()

        # 使用现有解析器获取基础参数
        parsed = self._engine.process(prompt)
        base_params = parsed["params"]

        # 提取各类信息
        constraints = self._extract_constraints(prompt, lower)
        priorities = self._extract_priorities(lower)
        requirements = self._extract_requirements(lower, constraints)
        assembly = self._extract_assembly_intent(lower)
        constraint_intent = self._extract_constraint_intent(lower)

        return DesignIntent(
            object=parsed["type"],
            constraints=constraints,
            priority=priorities,
            base_params=base_params,
            requirements=requirements,
            assembly_intent=assembly,
            constraint_intent=constraint_intent,
            original_prompt=prompt,
        )

    def _extract_constraints(self, prompt: str, lower: str) -> dict[str, Any]:
        """提取设计约束。"""
        constraints: dict[str, Any] = {}

        # 螺栓规格
        screw_match = re.search(r"[mM](\d+(?:\.\d+)?)", prompt)
        if screw_match:
            constraints["screw"] = f"M{screw_match.group(1)}"

        # 载荷
        for kw, level in LOAD_KEYWORDS.items():
            if kw in lower:
                constraints["load"] = level
                break

        # 材料
        for kw, mat in MATERIAL_KEYWORDS.items():
            if kw in lower:
                constraints["material"] = mat
                break

        # 轴承
        bearing_match = re.search(r"(608|625|6001)\s*轴承", prompt)
        if bearing_match:
            constraints["bearing"] = bearing_match.group(1)

        # 电机
        motor_match = re.search(r"(nema\s*17|nema\s*23|nema\s*34)", lower)
        if motor_match:
            constraints["motor_type"] = motor_match.group(1).replace(" ", "").upper()

        return constraints

    def _extract_priorities(self, lower: str) -> list[str]:
        """提取设计优先级。"""
        priorities: list[str] = []
        for kw, priority in PRIORITY_KEYWORDS.items():
            if kw in lower and priority not in priorities:
                priorities.append(priority)
        if not priorities:
            priorities = ["rigid", "printable", "lightweight"]
        return priorities

    def _extract_requirements(self, lower: str, constraints: dict[str, Any]) -> dict[str, Any]:
        """提取设计需求。"""
        requirements: dict[str, Any] = {}
        requirements["load"] = constraints.get("load", "medium")
        requirements["material"] = constraints.get("material", "PLA")
        requirements["multi_variant"] = any(
            kw in lower for kw in ["多种方案", "多个方案", "对比", "比较", "方案", "多方案"]
        )
        return requirements

    def _extract_assembly_intent(self, lower: str) -> list[str]:
        """提取装配意图。"""
        intents: list[str] = []
        for kw, intent in ASSEMBLY_KEYWORDS.items():
            if kw in lower:
                intents.append(intent)
        return intents

    def _extract_constraint_intent(self, lower: str) -> list[str]:
        """提取约束意图。"""
        intents: list[str] = []
        for kw, intent in CONSTRAINT_KEYWORDS.items():
            if kw in lower:
                intents.append(intent)
        return intents
