"""装配约束求解器 - 检查装配关系的合理性"""

from dataclasses import dataclass


@dataclass
class AssemblyConstraint:
    """装配约束定义"""
    type: str           # "fixed_to" | "aligned_with" | "inserted_fit" | "sliding_fit"
    part_a: str
    part_b: str
    clearance: float = 0.2  # mm


# 装配约束类型及其允许的间隙范围
CONSTRAINT_TYPES = {
    "fixed_to":       {"min_clearance": 0.0, "max_clearance": 0.0, "description": "固定连接"},
    "aligned_with":   {"min_clearance": 0.1, "max_clearance": 0.5, "description": "对齐配合"},
    "inserted_fit":   {"min_clearance": -0.05, "max_clearance": 0.1, "description": "压入配合"},
    "sliding_fit":    {"min_clearance": 0.1, "max_clearance": 0.5, "description": "滑动配合"},
    "clearance_fit":  {"min_clearance": 0.2, "max_clearance": 1.0, "description": "间隙配合"},
}


@dataclass
class ConstraintViolation:
    constraint: AssemblyConstraint
    message: str
    severity: str = "error"


def check_constraint(constraint: AssemblyConstraint) -> list[ConstraintViolation]:
    """检查单个约束是否合理"""
    violations = []
    spec = CONSTRAINT_TYPES.get(constraint.type)

    if not spec:
        violations.append(ConstraintViolation(
            constraint=constraint,
            message=f"未知约束类型: {constraint.type}",
            severity="warning",
        ))
        return violations

    if constraint.clearance < spec["min_clearance"]:
        violations.append(ConstraintViolation(
            constraint=constraint,
            message=f"{constraint.type} 间隙 {constraint.clearance}mm 小于最小值 {spec['min_clearance']}mm",
            severity="error",
        ))

    if constraint.clearance > spec["max_clearance"]:
        violations.append(ConstraintViolation(
            constraint=constraint,
            message=f"{constraint.type} 间隙 {constraint.clearance}mm 大于最大值 {spec['max_clearance']}mm",
            severity="warning",
        ))

    return violations


def check_assembly_constraints(constraints: list[dict]) -> dict:
    """检查所有装配约束

    Args:
        constraints: 约束列表 [{"type": "fixed_to", "part_a": "motor", "part_b": "bracket"}, ...]

    Returns:
        {"valid": bool, "violations": [...]}
    """
    all_violations = []

    for c in constraints:
        constraint = AssemblyConstraint(
            type=c.get("type", ""),
            part_a=c.get("part_a", ""),
            part_b=c.get("part_b", ""),
            clearance=c.get("clearance", 0.2),
        )
        violations = check_constraint(constraint)
        all_violations.extend(violations)

    has_error = any(v.severity == "error" for v in all_violations)

    return {
        "valid": not has_error,
        "violations": [
            {"parts": f"{v.constraint.part_a} → {v.constraint.part_b}", "type": v.constraint.type,
             "message": v.message, "severity": v.severity}
            for v in all_violations
        ],
    }


def detect_loops(parts: list[str], constraints: list[dict]) -> list[list[str]]:
    """检测装配中的约束环（可能导致过约束）"""
    # 简单的邻接表构建
    adj: dict[str, list[str]] = {p: [] for p in parts}
    for c in constraints:
        a, b = c.get("part_a", ""), c.get("part_b", "")
        if a in adj and b in adj:
            adj[a].append(b)
            adj[b].append(a)

    # DFS 检测环
    visited = set()
    loops = []

    def dfs(node, path):
        visited.add(node)
        for neighbor in adj.get(node, []):
            if neighbor in path:
                # 找到环
                idx = path.index(neighbor)
                loops.append(path[idx:] + [neighbor])
            elif neighbor not in visited:
                dfs(neighbor, path + [neighbor])

    for part in parts:
        if part not in visited:
            dfs(part, [part])

    return loops


# ============================================================
# Mate 约束集成
# ============================================================

def check_mate_constraints(mates: list[dict]) -> dict:
    """检查 Mate 约束列表。

    Args:
        mates: [{"type": "coincident", "source_part": "motor", "source_anchor": "shaft_axis",
                 "target_part": "mount", "target_anchor": "shaft_axis"}, ...]

    Returns:
        {"valid": bool, "results": [...]}
    """
    from ..engineering.assembly.mate import MateConstraint, solve_mate_chain
    from ..core.models import Part

    mate_objects = [
        MateConstraint(
            type=m.get("type", "coincident"),
            source_part=m.get("source_part", ""),
            source_anchor=m.get("source_anchor", ""),
            target_part=m.get("target_part", ""),
            target_anchor=m.get("target_anchor", ""),
            value=m.get("value", 0.0),
        )
        for m in mates
    ]

    # 构建空 Part 用于锚点查找（实际使用时应传入真实零件）
    parts_dict: dict[str, Part] = {}
    results = solve_mate_chain(mate_objects, parts_dict)

    has_error = any(not r.get("valid", False) for r in results)
    return {
        "valid": not has_error,
        "results": results,
    }
