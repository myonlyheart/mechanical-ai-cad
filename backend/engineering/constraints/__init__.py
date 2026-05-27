"""Constraints module - 约束系统。"""

from .dependency_graph import DependencyGraph, DependencyNode, NodeType
from .dirty_flag import DirtyFlagManager, DirtyNode
from .solver import (
    Constraint, solve_constraint, parse_nl_constraints,
    solve_coincident, solve_parallel, solve_perpendicular,
    solve_distance, solve_angle, solve_tangent,
)

__all__ = [
    "DependencyGraph", "DependencyNode", "NodeType",
    "DirtyFlagManager", "DirtyNode",
    "Constraint", "solve_constraint", "parse_nl_constraints",
    "solve_coincident", "solve_parallel", "solve_perpendicular",
    "solve_distance", "solve_angle", "solve_tangent",
]
