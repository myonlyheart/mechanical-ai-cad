"""tests/test_constraints.py - 约束系统测试（dependency graph, dirty flag, solver）。"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.engineering.constraints.dependency_graph import DependencyGraph
from backend.engineering.constraints.dirty_flag import DirtyFlagManager
from backend.engineering.constraints.solver import (
    Constraint, solve_constraint, solve_coincident, solve_parallel,
    solve_distance, parse_nl_constraints,
)
from backend.core.models import Anchor


# ============================================================
# DependencyGraph
# ============================================================

class TestDependencyGraph:
    def test_add_node(self):
        g = DependencyGraph()
        id_a = g.add_node("A")
        id_b = g.add_node("B")
        assert id_a != id_b

    def test_add_edge(self):
        g = DependencyGraph()
        a = g.add_node("A")
        b = g.add_node("B")
        g.add_edge(a, b)
        assert b in g.get_dependents(a)

    def test_topological_order(self):
        g = DependencyGraph()
        a = g.add_node("A")
        b = g.add_node("B")
        c = g.add_node("C")
        g.add_edge(a, b)  # a → b
        g.add_edge(b, c)  # b → c
        order = g.get_topological_order()
        # topo order: a before b before c
        assert order.index(a) < order.index(b)
        assert order.index(b) < order.index(c)

    def test_cycle_detection(self):
        g = DependencyGraph()
        a = g.add_node("A")
        b = g.add_node("B")
        g.add_edge(a, b)
        g.add_edge(b, a)
        assert g.has_cycle() is True

    def test_no_cycle(self):
        g = DependencyGraph()
        a = g.add_node("A")
        b = g.add_node("B")
        g.add_edge(a, b)
        assert g.has_cycle() is False

    def test_get_all_dependents(self):
        g = DependencyGraph()
        a = g.add_node("A")
        b = g.add_node("B")
        c = g.add_node("C")
        g.add_edge(a, b)  # a → b
        g.add_edge(b, c)  # b → c
        # dependents of a: following a → b → c
        affected = g.get_all_dependents(a)
        assert b in affected
        assert c in affected

    def test_get_dependencies(self):
        g = DependencyGraph()
        a = g.add_node("A")
        b = g.add_node("B")
        g.add_edge(a, b)  # a → b
        # dependencies of a: nodes that point to a (none)
        deps = g.get_dependencies(a)
        assert len(deps) == 0
        # but b is a dependent of a
        dependents = g.get_dependents(a)
        assert b in dependents


# ============================================================
# DirtyFlagManager
# ============================================================

class TestDirtyFlagManager:
    def test_mark_dirty(self):
        g = DependencyGraph()
        a = g.add_node("A")
        b = g.add_node("B")
        mgr = DirtyFlagManager(g)
        mgr.mark_dirty(a)
        assert mgr.is_dirty(a)
        assert not mgr.is_dirty(b)

    def test_propagate_dirty(self):
        g = DependencyGraph()
        a = g.add_node("A")
        b = g.add_node("B")
        g.add_edge(b, a)  # b → a: b changes propagate to a
        mgr = DirtyFlagManager(g)
        mgr.mark_dirty(b)
        assert mgr.is_dirty(a)  # propagated via b → a

    def test_mark_clean(self):
        g = DependencyGraph()
        a = g.add_node("A")
        mgr = DirtyFlagManager(g)
        mgr.mark_dirty(a)
        mgr.mark_clean(a)
        assert not mgr.is_dirty(a)

    def test_get_dirty_nodes(self):
        g = DependencyGraph()
        a = g.add_node("A")
        b = g.add_node("B")
        c = g.add_node("C")
        mgr = DirtyFlagManager(g)
        mgr.mark_dirty(a)
        mgr.mark_dirty(c)
        dirty = mgr.get_dirty_nodes()
        dirty_ids = [n.node_id for n in dirty]
        assert a in dirty_ids
        assert c in dirty_ids
        assert b not in dirty_ids

    def test_clear_all(self):
        g = DependencyGraph()
        a = g.add_node("A")
        mgr = DirtyFlagManager(g)
        mgr.mark_dirty(a)
        mgr.clear_all()
        assert not mgr.is_dirty(a)


# ============================================================
# Constraint Solver
# ============================================================

class TestConstraintSolver:
    def test_solve_coincident(self):
        src = Anchor(name="s", position=(0, 0, 0))
        tgt = Anchor(name="t", position=(10, 0, 0))
        result = solve_coincident(src, tgt)
        assert result["valid"] is True
        assert result["translation"] == (10, 0, 0)

    def test_solve_parallel_aligned(self):
        src = Anchor(name="s", direction=(0, 0, 1))
        tgt = Anchor(name="t", direction=(0, 0, 1))
        result = solve_parallel(src, tgt)
        assert result["valid"] is True

    def test_solve_parallel_not_aligned(self):
        src = Anchor(name="s", direction=(0, 0, 1))
        tgt = Anchor(name="t", direction=(1, 0, 0))
        result = solve_parallel(src, tgt)
        assert result["valid"] is False

    def test_solve_distance(self):
        src = Anchor(name="s", position=(0, 0, 0))
        tgt = Anchor(name="t", position=(10, 0, 0))
        result = solve_distance(src, tgt, 20.0)
        assert result["valid"] is True

    def test_solve_constraint_dispatch(self):
        c = Constraint(type="coincident")
        src = Anchor(name="s", position=(0, 0, 0))
        tgt = Anchor(name="t", position=(5, 5, 0))
        result = solve_constraint(c, src, tgt)
        assert result["valid"] is True

    def test_solve_constraint_unknown_type(self):
        c = Constraint(type="unknown")
        result = solve_constraint(c, Anchor(), Anchor())
        assert result["valid"] is False

    def test_parse_nl_symmetry(self):
        constraints = parse_nl_constraints("左右对称")
        assert len(constraints) > 0
        assert constraints[0].type == "parallel"

    def test_parse_nl_center(self):
        constraints = parse_nl_constraints("孔居中")
        assert len(constraints) > 0
        assert constraints[0].type == "coincident"

    def test_parse_nl_parallel(self):
        constraints = parse_nl_constraints("保持平行")
        assert len(constraints) > 0
        assert constraints[0].type == "parallel"

    def test_parse_nl_empty(self):
        constraints = parse_nl_constraints("随便做个零件")
        assert len(constraints) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
