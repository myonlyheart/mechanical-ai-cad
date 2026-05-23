"""CAD module for parametric part generation."""

from .base_part import BasePart, PartParams
from .bracket_generator import LBracket, LBracketParams, TBracket, TBracketParams
from .gear_generator import SpurGear, SpurGearParams
from .motor_mount import NEMA17Mount, NEMA17MountParams
from .hole_utils import add_hole, add_counterbore, add_countersink, add_slot, add_pattern_holes
from .export_utils import export_stl, export_step, export_obj

__all__ = [
    "BasePart", "PartParams",
    "LBracket", "LBracketParams",
    "TBracket", "TBracketParams",
    "SpurGear", "SpurGearParams",
    "NEMA17Mount", "NEMA17MountParams",
    "add_hole", "add_counterbore", "add_countersink", "add_slot", "add_pattern_holes",
    "export_stl", "export_step", "export_obj",
]
