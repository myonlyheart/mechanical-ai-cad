"""tests/test_models.py - 核心数据结构测试。"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.core.models import Anchor, Part, Assembly


class TestAnchor:
    def test_default_values(self):
        a = Anchor()
        assert a.type == "point"
        assert a.position == (0.0, 0.0, 0.0)
        assert a.direction == (0.0, 0.0, 1.0)
        assert len(a.id) == 8  # uuid 8 chars

    def test_custom_values(self):
        a = Anchor(name="test", type="face", position=(1, 2, 3), direction=(0, 1, 0))
        assert a.name == "test"
        assert a.type == "face"
        assert a.position == (1, 2, 3)
        assert a.direction == (0, 1, 0)

    def test_auto_id(self):
        a1 = Anchor(name="a")
        a2 = Anchor(name="b")
        assert a1.id != a2.id

    def test_metadata(self):
        a = Anchor(name="hole", metadata={"diameter": 6.5})
        assert a.metadata["diameter"] == 6.5


class TestPart:
    def test_default_values(self):
        p = Part()
        assert p.name == ""
        assert p.anchors == []
        assert p.parameters == {}

    def test_get_anchor(self):
        anchors = [
            Anchor(name="face1", type="face"),
            Anchor(name="axis1", type="axis"),
        ]
        p = Part(name="bracket", anchors=anchors)
        assert p.get_anchor("face1") is not None
        assert p.get_anchor("face1").type == "face"
        assert p.get_anchor("nonexistent") is None

    def test_get_anchors_by_type(self):
        anchors = [
            Anchor(name="f1", type="face"),
            Anchor(name="f2", type="face"),
            Anchor(name="a1", type="axis"),
        ]
        p = Part(anchors=anchors)
        faces = p.get_anchors_by_type("face")
        assert len(faces) == 2
        axes = p.get_anchors_by_type("axis")
        assert len(axes) == 1

    def test_to_dict(self):
        p = Part(name="gear", part_type="gear", parameters={"teeth": 20})
        d = p.to_dict()
        assert d["name"] == "gear"
        assert d["part_type"] == "gear"
        assert d["parameters"]["teeth"] == 20

    def test_from_dict_roundtrip(self):
        p = Part(
            name="mount", part_type="motor_mount",
            parameters={"height": 40},
            anchors=[Anchor(name="face", type="face")],
        )
        d = p.to_dict()
        p2 = Part.from_dict(d)
        assert p2.name == "mount"
        assert p2.part_type == "motor_mount"
        assert len(p2.anchors) == 1
        assert p2.anchors[0].name == "face"


class TestAssembly:
    def test_add_part(self):
        a = Assembly(name="robot")
        p1 = Part(name="base")
        p2 = Part(name="motor")
        a.add_part(p1)
        a.add_part(p2)
        assert len(a.children) == 2

    def test_get_part(self):
        a = Assembly(name="robot")
        p = Part(name="arm")
        a.add_part(p)
        assert a.get_part("arm") is not None
        assert a.get_part("leg") is None

    def test_add_constraint(self):
        a = Assembly(name="robot")
        a.add_constraint({"type": "coincident", "source": "base", "target": "motor"})
        assert len(a.constraints) == 1

    def test_to_dict(self):
        a = Assembly(name="test", children=[Part(name="p1")])
        d = a.to_dict()
        assert d["name"] == "test"
        assert d["metadata"]["part_count"] == 1
        assert d["metadata"]["constraint_count"] == 0

    def test_from_dict_roundtrip(self):
        a = Assembly(
            name="robot",
            children=[Part(name="base", part_type="bracket")],
            constraints=[{"type": "concentric"}],
        )
        d = a.to_dict()
        a2 = Assembly.from_dict(d)
        assert a2.name == "robot"
        assert len(a2.children) == 1
        assert a2.children[0].name == "base"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
