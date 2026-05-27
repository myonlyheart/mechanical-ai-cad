"""Validation module - 工程校验系统。"""

from .geometry import (
    ValidationError, GeometryValidationResult,
    validate_geometry,
    check_self_intersection, check_zero_thickness,
    check_non_manifold, check_topology,
)
from .manufacturing import (
    ManufacturingIssue, ManufacturingProcess,
    validate_manufacturing,
    check_wall_thickness, check_hole_diameter,
    check_overhang_angle, check_draft_angle,
)
from .collision import (
    AABB, CollisionResult,
    compute_aabb, check_collision_pair,
    check_assembly_collisions, check_hole_overlap,
)

__all__ = [
    "ValidationError", "GeometryValidationResult", "validate_geometry",
    "check_self_intersection", "check_zero_thickness",
    "check_non_manifold", "check_topology",
    "ManufacturingIssue", "ManufacturingProcess", "validate_manufacturing",
    "check_wall_thickness", "check_hole_diameter",
    "check_overhang_angle", "check_draft_angle",
    "AABB", "CollisionResult", "compute_aabb", "check_collision_pair",
    "check_assembly_collisions", "check_hole_overlap",
]
