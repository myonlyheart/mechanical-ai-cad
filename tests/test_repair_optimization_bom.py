"""tests/test_repair_optimization_bom.py - 修复、优化、BOM 测试。"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.engineering.repair.engine import (
    RepairSuggestion, RepairResult, RepairRule,
    generate_suggestions, auto_repair, full_repair_pipeline,
    REPAIR_RULES,
)
from backend.engineering.optimization.variants import (
    ScoringWeights, score_manufacturability, score_printability,
    score_strength, score_cost, score_weight, score_variant,
    generate_variants, compare_variants, recommend_variant,
)
from backend.engineering.bom.generator import (
    BOMItem, BOM, generate_bom_from_parts, generate_bom_from_assembly,
    bom_to_csv, bom_to_dict_list, _part_fingerprint, _generate_part_number,
)


# ============================================================
# Repair Engine
# ============================================================

class TestRepairEngine:
    def test_suggestion_to_dict(self):
        s = RepairSuggestion(problem="too thin", solution="increase thickness")
        d = s.to_dict()
        assert d["problem"] == "too thin"

    def test_result_to_dict(self):
        r = RepairResult(
            original_params={}, repaired_params={},
            suggestions=[], applied_fixes=["fixed wall"],
        )
        d = r.to_dict()
        assert len(d["applied_fixes"]) == 1

    def test_generate_suggestions(self):
        params = {"thickness": 0.5}
        issues = [{"code": "wall_too_thin", "message": "too thin", "severity": "error"}]
        suggestions = generate_suggestions(params, issues)
        assert len(suggestions) > 0

    def test_generate_suggestions_unknown(self):
        params = {}
        issues = [{"code": "unknown_issue", "message": "something"}]
        suggestions = generate_suggestions(params, issues)
        # generates a generic suggestion even for unknown issues
        assert len(suggestions) == 1
        assert suggestions[0].auto_fixable is False

    def test_auto_repair_wall_thin(self):
        params = {"thickness": 0.5, "material": "PLA"}
        issues = [{"code": "wall_too_thin", "severity": "error"}]
        result = auto_repair(params, issues)
        assert len(result.applied_fixes) > 0
        assert result.repaired_params["thickness"] > 0.5

    def test_auto_repair_hole_small(self):
        params = {"mounting_hole_diameter": 1.0}
        issues = [{"code": "hole_too_small", "severity": "error"}]
        result = auto_repair(params, issues)
        assert result.repaired_params["mounting_hole_diameter"] > 1.0

    def test_repair_rules_registry(self):
        assert "wall_too_thin" in REPAIR_RULES
        assert "hole_too_small" in REPAIR_RULES
        assert isinstance(REPAIR_RULES["wall_too_thin"], RepairRule)


# ============================================================
# Optimization / Variants
# ============================================================

class TestOptimization:
    def test_scoring_weights_presets(self):
        lw = ScoringWeights.lightweight()
        assert lw.weight > lw.strength
        hs = ScoringWeights.high_strength()
        assert hs.strength > hs.weight

    def test_score_manufacturability(self):
        score = score_manufacturability({"wall_thickness": 2.0, "overhang_angle": 30})
        assert 0 <= score <= 100

    def test_score_printability(self):
        score = score_printability({"overhang_angle": 20, "wall_thickness": 2.0})
        assert 0 <= score <= 100

    def test_score_strength(self):
        score = score_strength({"wall_thickness": 3.0, "base_thickness": 5.0})
        assert 0 <= score <= 100

    def test_score_cost(self):
        score = score_cost({"weight_g": 50, "material": "PLA"})
        assert 0 <= score <= 100

    def test_score_weight(self):
        score = score_weight({"weight_g": 30})
        assert 0 <= score <= 100

    def test_score_variant(self):
        params = {
            "wall_thickness": 2.0, "overhang_angle": 30,
            "base_thickness": 5.0, "weight_g": 40, "material": "PLA",
        }
        result = score_variant(params)
        assert 0 <= result["total"] <= 100
        assert result["grade"] in ("A", "B", "C", "D", "F")
        assert "breakdown" in result

    def test_compare_variants(self):
        variants = [
            {
                "design_id": "v1", "name": "light",
                "scores": {
                    "total": 75, "grade": "B",
                    "breakdown": {"manufacturability": 80, "printability": 70, "strength": 60, "cost": 80, "weight": 90},
                },
                "constraint_check": {"valid": True},
            },
            {
                "design_id": "v2", "name": "strong",
                "scores": {
                    "total": 85, "grade": "A",
                    "breakdown": {"manufacturability": 80, "printability": 70, "strength": 90, "cost": 70, "weight": 60},
                },
                "constraint_check": {"valid": True},
            },
        ]
        comparison = compare_variants(variants)
        assert len(comparison) == 2
        assert comparison[0]["design_id"] == "v1"

    def test_recommend_variant(self):
        variants = [
            {"design_id": "v2", "scores": {"total": 90}},
            {"design_id": "v1", "scores": {"total": 70}},
        ]
        rec = recommend_variant(variants)
        assert rec == "v2"  # first (highest scored after sort)


# ============================================================
# BOM Generator
# ============================================================

class TestBOMGenerator:
    def test_part_fingerprint(self):
        fp1 = _part_fingerprint("fastener", {"size": "M6"})
        fp2 = _part_fingerprint("fastener", {"size": "M6"})
        fp3 = _part_fingerprint("fastener", {"size": "M8"})
        assert fp1 == fp2
        assert fp1 != fp3

    def test_generate_part_number(self):
        pn = _generate_part_number(0, "bracket")
        assert pn.startswith("BRK")
        pn2 = _generate_part_number(1, "gear")
        assert pn2.startswith("GAR")
        pn3 = _generate_part_number(0, "motor_mount")
        assert pn3.startswith("MTM")

    def test_generate_bom_from_parts(self):
        parts = [
            {"name": "bolt_M6", "part_type": "fastener", "parameters": {"size": "M6"}, "metadata": {}},
            {"name": "bolt_M6_dup", "part_type": "fastener", "parameters": {"size": "M6"}, "metadata": {}},
            {"name": "bracket", "part_type": "bracket", "parameters": {}, "metadata": {}},
        ]
        bom = generate_bom_from_parts(parts)
        assert bom.total_parts == 3
        assert bom.unique_parts == 2

    def test_generate_bom_from_assembly(self):
        from backend.core.models import Assembly, Part
        asm = Assembly(
            name="robot",
            children=[
                Part(name="base", part_type="bracket"),
                Part(name="motor", part_type="motor_mount"),
            ],
        )
        bom = generate_bom_from_assembly(asm)
        assert bom.total_parts == 2

    def test_bom_to_csv(self):
        bom = BOM(
            items=[
                BOMItem(part_number="BRK-001", part_name="bracket", material="PLA", quantity=2, weight_g=50),
                BOMItem(part_number="MTM-001", part_name="motor mount", material="ABS", quantity=1, weight_g=80),
            ]
        )
        csv_str = bom_to_csv(bom)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 5  # header + 2 items + empty + summary
        assert "BRK-001" in lines[1]

    def test_bom_to_dict_list(self):
        bom = BOM(
            items=[BOMItem(part_number="X-001", part_name="test", material="PLA", quantity=1)]
        )
        dicts = bom_to_dict_list(bom)
        assert len(dicts) == 1
        assert dicts[0]["part_number"] == "X-001"
        assert dicts[0]["part_name"] == "test"

    def test_bom_computed_properties(self):
        bom = BOM(
            items=[
                BOMItem(part_name="a", quantity=3, weight_g=10),
                BOMItem(part_name="b", quantity=2, weight_g=20),
            ]
        )
        assert bom.total_parts == 5
        assert bom.unique_parts == 2
        assert bom.total_weight_g == 70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
