"""Engineering module - 工程层核心。"""

from .assembly import (
    Transform3D, AssemblyNode, AssemblyTree,
    MateConstraint, MateType,
    create_coincident_mate, create_concentric_mate, create_parallel_mate,
    solve_mate, solve_mate_chain,
)
from .constraints import (
    DependencyGraph, DirtyFlagManager,
    Constraint, solve_constraint, parse_nl_constraints,
)
from .validation import (
    validate_geometry, validate_manufacturing,
    check_assembly_collisions, AABB,
)
from .repair import (
    RepairSuggestion, RepairResult,
    auto_repair, full_repair_pipeline,
)
from .optimization import (
    ScoringWeights, score_variant, generate_variants,
    compare_variants, recommend_variant,
)
from .bom import (
    BOM, BOMItem,
    generate_bom_from_parts, generate_bom_from_assembly,
    bom_to_csv, save_bom_csv,
)

__all__ = [
    "Transform3D", "AssemblyNode", "AssemblyTree",
    "MateConstraint", "MateType",
    "create_coincident_mate", "create_concentric_mate", "create_parallel_mate",
    "solve_mate", "solve_mate_chain",
    "DependencyGraph", "DirtyFlagManager",
    "Constraint", "solve_constraint", "parse_nl_constraints",
    "validate_geometry", "validate_manufacturing",
    "check_assembly_collisions", "AABB",
    "RepairSuggestion", "RepairResult",
    "auto_repair", "full_repair_pipeline",
    "ScoringWeights", "score_variant", "generate_variants",
    "compare_variants", "recommend_variant",
    "BOM", "BOMItem",
    "generate_bom_from_parts", "generate_bom_from_assembly",
    "bom_to_csv", "save_bom_csv",
]
