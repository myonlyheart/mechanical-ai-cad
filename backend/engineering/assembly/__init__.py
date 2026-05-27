"""Assembly module - 装配系统。"""

from .anchors import (
    create_point_anchor, create_face_anchor, create_axis_anchor,
    create_hole_center_anchor, create_edge_anchor,
    nema17_mount_anchors, l_bracket_anchors, t_bracket_anchors,
)
from .tree import Transform3D, AssemblyNode, AssemblyTree
from .mate import (
    MateType, MateConstraint,
    create_coincident_mate, create_concentric_mate,
    create_parallel_mate, create_distance_mate,
    solve_mate, solve_mate_chain,
)

__all__ = [
    "create_point_anchor", "create_face_anchor", "create_axis_anchor",
    "create_hole_center_anchor", "create_edge_anchor",
    "nema17_mount_anchors", "l_bracket_anchors", "t_bracket_anchors",
    "Transform3D", "AssemblyNode", "AssemblyTree",
    "MateType", "MateConstraint",
    "create_coincident_mate", "create_concentric_mate",
    "create_parallel_mate", "create_distance_mate",
    "solve_mate", "solve_mate_chain",
]
