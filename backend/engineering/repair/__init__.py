"""Repair module - 自动修复引擎。"""

from .engine import (
    RepairSuggestion, RepairResult, RepairRule,
    generate_suggestions, auto_repair, full_repair_pipeline,
)

__all__ = [
    "RepairSuggestion", "RepairResult", "RepairRule",
    "generate_suggestions", "auto_repair", "full_repair_pipeline",
]
