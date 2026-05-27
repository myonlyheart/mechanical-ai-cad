"""机械依赖推理模块。"""

from .dependency_rules import (
    DEPENDENCY_RULES,
    DependencyRule,
    get_rules_for_source,
    get_rules_for_target,
    get_dependency_chain,
    validate_dependency,
)
from .engine import (
    MechanicalReasoningEngine,
    ReasoningResult,
    ReasoningStep,
    DependencyNode,
    reason_part,
    reason_assembly,
)
from .systems import (
    SYSTEM_TEMPLATES,
    SystemTemplate,
    detect_system,
    list_systems,
)

__all__ = [
    "DEPENDENCY_RULES",
    "DependencyRule",
    "get_rules_for_source",
    "get_rules_for_target",
    "get_dependency_chain",
    "validate_dependency",
    "MechanicalReasoningEngine",
    "ReasoningResult",
    "ReasoningStep",
    "DependencyNode",
    "reason_part",
    "reason_assembly",
    "SYSTEM_TEMPLATES",
    "SystemTemplate",
    "detect_system",
    "list_systems",
]
