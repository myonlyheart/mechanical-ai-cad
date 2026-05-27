"""tests/test_validation.py - 校验系统测试（geometry, manufacturing, collision）。"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.engineering.validation.geometry import (
    GeometryValidationResult, ValidationError, ValidationSeverity,
    validate_geometry, check_self_intersection, check_zero_thickness,
)
from backend.engineering.validation.manufacturing import (
    ManufacturingProcess, ManufacturingIssue,
    check_wall_thickness, check_hole_diameter, check_overhang_angle,
    check_draft_angle, check_min_feature_size, validate_manufacturing,
    FDM_MIN_WALL_THICKNESS, FDM_MIN_HOLE_DIAMETER, FDM_MAX_OVERHANG_ANGLE,
)
from backend.engineering.validation.collision import (
    AABB, check_assembly_collisions, check_hole_overlap,
)


# ============================================================
# Geometry Validation
# ============================================================

class TestGeometryValidation:
    def test_validate_none_geometry(self):
        result = validate_geometry(None)
        assert not result.valid
        assert any(e.code == "no_geometry" for e in result.errors)

    def test_check_self_intersection_none(self):
        result = check_self_intersection(None)
        assert not result.valid

    def test_validation_result_add_error(self):
        r = GeometryValidationResult()
        assert r.valid
        r.add_error("test", "test error")
        assert not r.valid
        assert len(r.errors) == 1

    def test_validation_result_add_warning(self):
        r = GeometryValidationResult()
        r.add_warning("test", "test warning")
        assert r.valid  # warnings don't invalidate
        assert len(r.warnings) == 1

    def test_validation_error_to_dict(self):
        e = ValidationError(code="test", message="msg", severity="error")
        d = e.to_dict()
        assert d["code"] == "test"
        assert d["severity"] == "error"

    def test_combined_result(self):
        result = GeometryValidationResult()
        result.add_error("e1", "error 1")
        d = result.to_dict()
        assert d["valid"] is False
        assert len(d["errors"]) == 1


# ============================================================
# Manufacturing Validation
# ============================================================

class TestManufacturingValidation:
    def test_wall_thickness_ok(self):
        issues = check_wall_thickness(3.0, "PLA", ManufacturingProcess.FDM_3D_PRINT)
        assert len(issues) == 0

    def test_wall_thickness_too_thin(self):
        issues = check_wall_thickness(0.5, "PLA", ManufacturingProcess.FDM_3D_PRINT)
        assert len(issues) > 0
        assert issues[0].code == "wall_too_thin"
        assert issues[0].severity == "error"

    def test_wall_thickness_warning(self):
        # 1.2 * 1.1 = 1.32 < 1.2 * 1.5 = 1.8 → warning
        issues = check_wall_thickness(1.3, "PLA", ManufacturingProcess.FDM_3D_PRINT)
        has_warning = any(i.severity == "warning" for i in issues)
        assert has_warning

    def test_wall_thickness_cnc(self):
        issues = check_wall_thickness(0.3, process=ManufacturingProcess.CNC_MILLING)
        assert any(i.code == "wall_too_thin" for i in issues)

    def test_wall_thickness_injection_too_thick(self):
        issues = check_wall_thickness(5.0, process=ManufacturingProcess.INJECTION_MOLDING)
        assert any(i.code == "wall_too_thick" for i in issues)

    def test_hole_diameter_ok(self):
        issues = check_hole_diameter(5.0, ManufacturingProcess.FDM_3D_PRINT)
        assert len(issues) == 0

    def test_hole_diameter_too_small(self):
        issues = check_hole_diameter(1.0, ManufacturingProcess.FDM_3D_PRINT)
        assert any(i.code == "hole_too_small" for i in issues)

    def test_overhang_ok(self):
        issues = check_overhang_angle(30)
        assert len(issues) == 0

    def test_overhang_too_large(self):
        issues = check_overhang_angle(60)
        assert any(i.code == "overhang_too_large" for i in issues)

    def test_draft_angle_ok(self):
        issues = check_draft_angle(2.0)
        assert len(issues) == 0

    def test_draft_angle_too_small(self):
        issues = check_draft_angle(0.5)
        assert any(i.code == "draft_too_small" for i in issues)

    def test_min_feature_size_ok(self):
        issues = check_min_feature_size(2.0)
        assert len(issues) == 0

    def test_min_feature_size_too_small(self):
        issues = check_min_feature_size(0.5)
        assert len(issues) > 0

    def test_validate_manufacturing_valid(self):
        result = validate_manufacturing({"thickness": 3.0, "material": "PLA", "hole_diameter": 5.0})
        assert result["valid"] is True

    def test_validate_manufacturing_invalid(self):
        result = validate_manufacturing({"thickness": 0.5, "material": "PLA", "hole_diameter": 1.0})
        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_manufacturing_issue_to_dict(self):
        issue = ManufacturingIssue(code="test", message="msg", severity="error")
        d = issue.to_dict()
        assert d["code"] == "test"


# ============================================================
# Collision Detection
# ============================================================

class TestCollisionDetection:
    def test_aabb_no_intersect(self):
        a = AABB(min_x=0, min_y=0, min_z=0, max_x=10, max_y=10, max_z=10)
        b = AABB(min_x=20, min_y=20, min_z=20, max_x=30, max_y=30, max_z=30)
        assert not a.intersects(b)

    def test_aabb_intersect(self):
        a = AABB(min_x=0, min_y=0, min_z=0, max_x=10, max_y=10, max_z=10)
        b = AABB(min_x=5, min_y=5, min_z=5, max_x=15, max_y=15, max_z=15)
        assert a.intersects(b)

    def test_aabb_touching(self):
        a = AABB(min_x=0, min_y=0, min_z=0, max_x=10, max_y=10, max_z=10)
        b = AABB(min_x=10, min_y=10, min_z=10, max_x=20, max_y=20, max_z=20)
        assert a.intersects(b)

    def test_aabb_intersection_volume(self):
        a = AABB(min_x=0, min_y=0, min_z=0, max_x=10, max_y=10, max_z=10)
        b = AABB(min_x=5, min_y=5, min_z=5, max_x=15, max_y=15, max_z=15)
        vol = a.intersection_volume(b)
        assert vol == 5 * 5 * 5

    def test_aabb_no_overlap_volume(self):
        a = AABB(min_x=0, min_y=0, min_z=0, max_x=10, max_y=10, max_z=10)
        b = AABB(min_x=20, min_y=20, min_z=20, max_x=30, max_y=30, max_z=30)
        assert a.intersection_volume(b) == 0

    def test_aabb_center(self):
        a = AABB(min_x=0, min_y=0, min_z=0, max_x=10, max_y=10, max_z=10)
        assert a.center == (5, 5, 5)

    def test_aabb_size(self):
        a = AABB(min_x=0, min_y=0, min_z=0, max_x=10, max_y=20, max_z=30)
        assert a.size == (10, 20, 30)

    def test_check_assembly_collisions(self):
        parts = [
            ("part_a", AABB(min_x=0, min_y=0, min_z=0, max_x=10, max_y=10, max_z=10)),
            ("part_b", AABB(min_x=5, min_y=5, min_z=5, max_x=15, max_y=15, max_z=15)),
            ("part_c", AABB(min_x=20, min_y=20, min_z=20, max_x=30, max_y=30, max_z=30)),
        ]
        result = check_assembly_collisions(parts)
        assert result["collision_count"] == 1
        assert len(result["collisions"]) == 1

    def test_check_assembly_no_collisions(self):
        parts = [
            ("a", AABB(min_x=0, min_y=0, min_z=0, max_x=10, max_y=10, max_z=10)),
            ("b", AABB(min_x=100, min_y=100, min_z=100, max_x=110, max_y=110, max_z=110)),
        ]
        result = check_assembly_collisions(parts)
        assert result["collision_count"] == 0

    def test_check_hole_overlap(self):
        parts = [
            {
                "name": "part_a",
                "anchors": [
                    {"name": "h1", "type": "hole_center", "position": (0, 0, 0), "metadata": {"diameter": 6.0}},
                ],
            },
            {
                "name": "part_b",
                "anchors": [
                    {"name": "h2", "type": "hole_center", "position": (2, 0, 0), "metadata": {"diameter": 6.0}},
                ],
            },
        ]
        overlaps = check_hole_overlap(parts)
        assert len(overlaps) > 0

    def test_check_hole_no_overlap(self):
        parts = [
            {
                "name": "part_a",
                "anchors": [
                    {"name": "h1", "type": "hole_center", "position": (0, 0, 0), "metadata": {"diameter": 6.0}},
                ],
            },
            {
                "name": "part_b",
                "anchors": [
                    {"name": "h2", "type": "hole_center", "position": (20, 0, 0), "metadata": {"diameter": 6.0}},
                ],
            },
        ]
        overlaps = check_hole_overlap(parts)
        assert len(overlaps) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
