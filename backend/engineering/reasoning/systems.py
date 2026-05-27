"""预定义机械系统模板。

将常见的机械系统描述映射为零件组合：
- "3:1 减速器" → 齿轮对 + 轴 + 轴承
- "XYZ 平台" → 导轨 + 丝杆 + 电机 × 3
- "旋转台" → 轴 + 轴承 + 齿轮 + 电机
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SystemTemplate:
    """机械系统模板。"""
    name: str
    keywords: list[str]
    description: str
    parts: list[dict[str, Any]]
    constraints: list[dict[str, str]] = field(default_factory=list)


SYSTEM_TEMPLATES: dict[str, SystemTemplate] = {
    "gear_reducer": SystemTemplate(
        name="齿轮减速器",
        keywords=["减速", "减速器", "减速机", "gear reducer", "reduction"],
        description="齿轮减速传动系统",
        parts=[
            {"part_type": "gear", "name": "主动齿轮", "params": {"gear_type": "spur", "module": 2}},
            {"part_type": "gear", "name": "从动齿轮", "params": {"gear_type": "spur", "module": 2}},
            {"part_type": "shaft", "name": "输入轴", "params": {}},
            {"part_type": "shaft", "name": "输出轴", "params": {}},
            {"part_type": "bearing", "name": "输入端轴承", "params": {}},
            {"part_type": "bearing", "name": "输出端轴承", "params": {}},
        ],
        constraints=[
            {"type": "gear_mesh", "a": "主动齿轮", "b": "从动齿轮", "rule": "模数相同"},
            {"type": "concentric", "a": "输入轴", "b": "主动齿轮", "rule": "孔径=轴径"},
            {"type": "concentric", "a": "输出轴", "b": "从动齿轮", "rule": "孔径=轴径"},
        ],
    ),
    "linear_stage": SystemTemplate(
        name="线性运动平台",
        keywords=["平台", "线性", "导轨", "滑台", "linear stage", "xyz"],
        description="线性导轨 + 丝杆驱动",
        parts=[
            {"part_type": "rail", "name": "线性导轨", "params": {}},
            {"part_type": "lead_screw", "name": "丝杆", "params": {}},
            {"part_type": "motor", "name": "驱动电机", "params": {"motor_name": "NEMA17"}},
            {"part_type": "coupling", "name": "联轴器", "params": {}},
            {"part_type": "bearing", "name": "丝杆支撑轴承", "params": {}},
        ],
        constraints=[
            {"type": "concentric", "a": "丝杆", "b": "联轴器", "rule": "轴径=孔径"},
            {"type": "concentric", "a": "驱动电机", "b": "联轴器", "rule": "轴径=孔径"},
        ],
    ),
    "rotary_table": SystemTemplate(
        name="旋转台",
        keywords=["旋转", "转台", "旋转台", "rotary", "turntable"],
        description="电机驱动的旋转平台",
        parts=[
            {"part_type": "motor", "name": "驱动电机", "params": {"motor_name": "NEMA17"}},
            {"part_type": "gear", "name": "主动齿轮", "params": {"gear_type": "spur", "module": 2}},
            {"part_type": "gear", "name": "从动齿轮", "params": {"gear_type": "spur", "module": 2}},
            {"part_type": "shaft", "name": "旋转轴", "params": {}},
            {"part_type": "bearing", "name": "上端轴承", "params": {}},
            {"part_type": "bearing", "name": "下端轴承", "params": {}},
        ],
        constraints=[
            {"type": "gear_mesh", "a": "主动齿轮", "b": "从动齿轮"},
            {"type": "concentric", "a": "旋转轴", "b": "从动齿轮"},
        ],
    ),
    "belt_drive": SystemTemplate(
        name="皮带传动",
        keywords=["皮带", "同步带", "belt", "pulley"],
        description="同步带传动系统",
        parts=[
            {"part_type": "pulley", "name": "主动轮", "params": {}},
            {"part_type": "pulley", "name": "从动轮", "params": {}},
            {"part_type": "shaft", "name": "输入轴", "params": {}},
            {"part_type": "shaft", "name": "输出轴", "params": {}},
            {"part_type": "bearing", "name": "输入端轴承", "params": {}},
            {"part_type": "bearing", "name": "输出端轴承", "params": {}},
        ],
        constraints=[
            {"type": "concentric", "a": "输入轴", "b": "主动轮"},
            {"type": "concentric", "a": "输出轴", "b": "从动轮"},
        ],
    ),
}


def detect_system(prompt: str) -> SystemTemplate | None:
    """从用户描述中检测机械系统类型。"""
    prompt_lower = prompt.lower()
    for template in SYSTEM_TEMPLATES.values():
        for kw in template.keywords:
            if kw.lower() in prompt_lower:
                return template
    return None


def list_systems() -> list[dict[str, Any]]:
    """列出所有可用的系统模板。"""
    return [
        {
            "id": key,
            "name": t.name,
            "description": t.description,
            "keywords": t.keywords,
            "parts_count": len(t.parts),
        }
        for key, t in SYSTEM_TEMPLATES.items()
    ]
