"""tests/test_ai_modules.py - AI 模块测试（parser, planner, reasoning）。"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.ai.parser.intent import DesignIntent
from backend.ai.planner.engine import EngineeringPlan
from backend.ai.reasoning.engine import ReasoningResult


# ============================================================
# DesignIntent
# ============================================================

class TestDesignIntent:
    def test_default_values(self):
        intent = DesignIntent()
        assert intent.object == ""
        assert intent.constraints == {}
        assert intent.priority == []

    def test_to_dict(self):
        intent = DesignIntent(
            object="bracket",
            constraints={"screw_spec": "M6"},
            priority=["lightweight"],
            original_prompt="做一个轻量化支架",
        )
        d = intent.to_dict()
        assert d["object"] == "bracket"
        assert d["constraints"]["screw_spec"] == "M6"
        assert "lightweight" in d["priority"]

    def test_with_assembly_intent(self):
        intent = DesignIntent(
            object="motor_mount",
            assembly_intent=["assemble", "bolt"],
            constraint_intent=["symmetric"],
        )
        d = intent.to_dict()
        assert "assemble" in d["assembly_intent"]
        assert "symmetric" in d["constraint_intent"]


# ============================================================
# EngineeringPlan
# ============================================================

class TestEngineeringPlan:
    def test_default_values(self):
        plan = EngineeringPlan()
        assert plan.part_type == ""
        assert plan.optimization_goal == "balanced"
        assert plan.designs == []

    def test_to_dict(self):
        plan = EngineeringPlan(
            part_type="bracket",
            base_params={"thickness": 5},
            optimization_goal="lightweight",
            constraints_to_apply=["manufacturing_check"],
        )
        d = plan.to_dict()
        assert d["part_type"] == "bracket"
        assert d["optimization_goal"] == "lightweight"
        assert "manufacturing_check" in d["constraints_to_apply"]

    def test_with_designs(self):
        plan = EngineeringPlan(
            part_type="gear",
            designs=[
                {"name": "standard", "params": {"teeth": 20}},
                {"name": "heavy", "params": {"teeth": 30}},
            ],
        )
        assert len(plan.designs) == 2


# ============================================================
# ReasoningResult
# ============================================================

class TestReasoningResult:
    def test_default_values(self):
        r = ReasoningResult()
        assert r.recommendation == ""
        assert r.variants == []
        assert r.reasoning_steps == []

    def test_to_dict(self):
        r = ReasoningResult(
            intent={"object": "bracket"},
            plan={"optimization_goal": "lightweight"},
            variants=[{"design_id": "v1"}],
            comparison=[{"design_id": "v1"}],
            recommendation="v1",
            reasoning_steps=["step 1", "step 2"],
        )
        d = r.to_dict()
        assert d["recommendation"] == "v1"
        assert len(d["reasoning_steps"]) == 2
        assert len(d["variants"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
