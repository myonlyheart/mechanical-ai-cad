"""tests/test_assembly.py - 装配系统测试（anchors, tree, mate）。"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.core.models import Anchor, Part
from backend.engineering.assembly.anchors import (
    create_point_anchor, create_face_anchor, create_axis_anchor,
    create_hole_center_anchor, create_edge_anchor,
    nema17_mount_anchors, l_bracket_anchors, t_bracket_anchors,
)
from backend.engineering.assembly.tree import Transform3D, AssemblyNode, AssemblyTree
from backend.engineering.assembly.mate import (
    MateConstraint, MateType,
    create_coincident_mate, create_concentric_mate,
    create_parallel_mate, create_distance_mate,
    solve_mate, solve_mate_chain,
)


# ============================================================
# Anchors
# ============================================================

class TestAnchors:
    def test_create_point_anchor(self):
        a = create_point_anchor("origin", (0, 0, 0))
        assert a.name == "origin"
        assert a.type == "point"
        assert a.position == (0, 0, 0)

    def test_create_face_anchor(self):
        a = create_face_anchor("top", (0, 0, 10), normal=(0, 0, 1))
        assert a.type == "face"
        assert a.direction == (0, 0, 1)

    def test_create_axis_anchor(self):
        a = create_axis_anchor("shaft", (0, 0, 0), direction=(0, 0, 1))
        assert a.type == "axis"

    def test_create_hole_center_anchor(self):
        a = create_hole_center_anchor("hole1", (10, 0, 0), diameter=6.5)
        assert a.type == "hole_center"
        assert a.metadata["diameter"] == 6.5

    def test_create_edge_anchor(self):
        a = create_edge_anchor("edge1", (5, 5, 0))
        assert a.type == "edge"

    def test_nema17_mount_anchors(self):
        anchors = nema17_mount_anchors()
        names = {a.name for a in anchors}
        assert "mount_face" in names
        assert "shaft_axis" in names
        assert "motor_hole_1" in names
        assert "base_face" in names
        assert len(anchors) == 7

    def test_l_bracket_anchors(self):
        anchors = l_bracket_anchors()
        names = {a.name for a in anchors}
        assert "vertical_face" in names
        assert "horizontal_face" in names
        assert len(anchors) == 6

    def test_t_bracket_anchors(self):
        anchors = t_bracket_anchors()
        assert len(anchors) == 4


# ============================================================
# Transform3D
# ============================================================

class TestTransform3D:
    def test_identity(self):
        t = Transform3D.identity()
        assert t.position == (0, 0, 0)
        assert t.scale == (1, 1, 1)

    def test_from_position(self):
        t = Transform3D.from_position(10, 20, 30)
        assert t.position == (10, 20, 30)

    def test_apply_to_point(self):
        t = Transform3D.from_position(5, 10, 15)
        p = t.apply_to_point((1, 2, 3))
        assert p == (6, 12, 18)

    def test_multiply(self):
        t1 = Transform3D.from_position(1, 2, 3)
        t2 = Transform3D.from_position(4, 5, 6)
        t3 = t1.multiply(t2)
        assert t3.position == (5, 7, 9)

    def test_to_dict(self):
        t = Transform3D.from_position(1, 2, 3)
        d = t.to_dict()
        assert d["position"] == (1, 2, 3)


# ============================================================
# AssemblyNode
# ============================================================

class TestAssemblyNode:
    def test_world_transform_no_parent(self):
        node = AssemblyNode(name="root", local_transform=Transform3D.from_position(10, 0, 0))
        assert node.world_transform.position == (10, 0, 0)

    def test_world_transform_with_parent(self):
        parent = AssemblyNode(name="parent", local_transform=Transform3D.from_position(10, 0, 0))
        child = AssemblyNode(name="child", local_transform=Transform3D.from_position(5, 0, 0))
        parent.add_child(child)
        assert child.world_transform.position == (15, 0, 0)

    def test_add_child(self):
        parent = AssemblyNode(name="parent")
        child = AssemblyNode(name="child")
        parent.add_child(child)
        assert child.parent is parent
        assert len(parent.children) == 1

    def test_remove_child(self):
        parent = AssemblyNode(name="parent")
        child = AssemblyNode(name="child")
        parent.add_child(child)
        removed = parent.remove_child(child.id)
        assert removed is child
        assert len(parent.children) == 0

    def test_find_node(self):
        root = AssemblyNode(name="root")
        child = AssemblyNode(name="motor")
        grandchild = AssemblyNode(name="shaft")
        root.add_child(child)
        child.add_child(grandchild)
        assert root.find_node("shaft") is grandchild
        assert root.find_node("nonexistent") is None

    def test_is_leaf(self):
        node = AssemblyNode(name="leaf")
        assert node.is_leaf()
        node.add_child(AssemblyNode(name="child"))
        assert not node.is_leaf()

    def test_get_depth(self):
        root = AssemblyNode(name="root")
        child = AssemblyNode(name="child")
        grandchild = AssemblyNode(name="grandchild")
        root.add_child(child)
        child.add_child(grandchild)
        assert root.get_depth() == 0
        assert child.get_depth() == 1
        assert grandchild.get_depth() == 2

    def test_get_all_parts(self):
        root = AssemblyNode(name="root")
        p1 = Part(name="base")
        p2 = Part(name="motor")
        root.add_child(AssemblyNode(name="base", part=p1))
        root.add_child(AssemblyNode(name="motor", part=p2))
        parts = root.get_all_parts()
        assert len(parts) == 2

    def test_to_dict(self):
        node = AssemblyNode(name="test", part=Part(name="bracket"))
        d = node.to_dict()
        assert d["name"] == "test"
        assert d["part"]["name"] == "bracket"


# ============================================================
# AssemblyTree
# ============================================================

class TestAssemblyTree:
    def test_add_part(self):
        tree = AssemblyTree("robot")
        p = Part(name="base", part_type="bracket")
        node = tree.add_part(p)
        assert node.name == "base"
        assert len(tree.root.children) == 1

    def test_add_part_to_parent(self):
        tree = AssemblyTree("robot")
        tree.add_subassembly("drive_unit")
        p = Part(name="motor")
        node = tree.add_part(p, parent_name="drive_unit")
        assert node.parent.name == "drive_unit"

    def test_add_part_invalid_parent(self):
        tree = AssemblyTree("robot")
        with pytest.raises(ValueError, match="未找到父节点"):
            tree.add_part(Part(name="x"), parent_name="nonexistent")

    def test_find(self):
        tree = AssemblyTree("robot")
        tree.add_part(Part(name="base"))
        assert tree.find("base") is not None
        assert tree.find("nope") is None

    def test_flat_list(self):
        tree = AssemblyTree("robot")
        tree.add_part(Part(name="base"))
        tree.add_part(Part(name="motor"))
        flat = tree.flat_list()
        assert len(flat) == 2
        names = [n["name"] for n in flat]
        assert "base" in names
        assert "motor" in names


# ============================================================
# Mate
# ============================================================

class TestMate:
    def test_create_coincident_mate(self):
        m = create_coincident_mate("motor", "mount_face", "bracket", "top_face")
        assert m.type == MateType.COINCIDENT
        assert m.source_part == "motor"

    def test_create_concentric_mate(self):
        m = create_concentric_mate("motor", "shaft", "bracket", "hole")
        assert m.type == MateType.CONCENTRIC

    def test_create_distance_mate(self):
        m = create_distance_mate("a", "p1", "b", "p2", 10.0)
        assert m.value == 10.0

    def test_solve_coincident(self):
        src = Anchor(name="s", position=(0, 0, 0))
        tgt = Anchor(name="t", position=(10, 20, 30))
        mate = create_coincident_mate("p1", "s", "p2", "t")
        result = solve_mate(mate, [src], [tgt])
        assert result["valid"] is True
        assert result["translation"] == (10, 20, 30)

    def test_solve_concentric(self):
        src = Anchor(name="s", position=(5, 5, 0))
        tgt = Anchor(name="t", position=(10, 10, 0))
        mate = create_concentric_mate("p1", "s", "p2", "t")
        result = solve_mate(mate, [src], [tgt])
        assert result["valid"] is True
        assert result["translation"] == (5, 5, 0)

    def test_solve_parallel_aligned(self):
        src = Anchor(name="s", direction=(0, 0, 1))
        tgt = Anchor(name="t", direction=(0, 0, 1))
        mate = create_parallel_mate("p1", "s", "p2", "t")
        result = solve_mate(mate, [src], [tgt])
        assert result["valid"] is True

    def test_solve_parallel_not_aligned(self):
        src = Anchor(name="s", direction=(0, 0, 1))
        tgt = Anchor(name="t", direction=(1, 0, 0))
        mate = create_parallel_mate("p1", "s", "p2", "t")
        result = solve_mate(mate, [src], [tgt])
        assert result["valid"] is False

    def test_solve_distance(self):
        src = Anchor(name="s", position=(0, 0, 0))
        tgt = Anchor(name="t", position=(10, 0, 0))
        mate = create_distance_mate("p1", "s", "p2", "t", 20.0)
        result = solve_mate(mate, [src], [tgt])
        assert result["valid"] is True

    def test_solve_missing_anchor(self):
        mate = create_coincident_mate("p1", "missing", "p2", "t")
        result = solve_mate(mate, [], [])
        assert result["valid"] is False

    def test_solve_mate_chain(self):
        p1 = Part(
            name="motor",
            anchors=[Anchor(name="face", position=(0, 0, 0))],
        )
        p2 = Part(
            name="bracket",
            anchors=[Anchor(name="top", position=(0, 0, 50))],
        )
        mates = [create_coincident_mate("motor", "face", "bracket", "top")]
        parts = {"motor": p1, "bracket": p2}
        results = solve_mate_chain(mates, parts)
        assert len(results) == 1
        assert results[0]["valid"] is True

    def test_to_dict(self):
        m = create_coincident_mate("a", "x", "b", "y")
        d = m.to_dict()
        assert d["type"] == "coincident"
        assert d["source_part"] == "a"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
