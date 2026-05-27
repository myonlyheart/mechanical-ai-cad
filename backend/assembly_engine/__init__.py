"""自动装配系统 - 零件识别、对齐求解、装配构建"""

from .alignment_solver import get_alignment_rules, solve_alignment
from .constraint_solver import check_assembly_constraints
from .assembly_builder import build_assembly_structure, generate_assembly_code


def build_assembly(parts: list[dict], constraints: list[dict]) -> dict:
    """完整装配流程

    Args:
        parts: 零件列表 [{"name": "motor", "part_type": "motor", "params": {...}}, ...]
        constraints: 装配约束列表 [{"type": "fixed_to", "part_a": "motor", "part_b": "bracket"}, ...]

    Returns:
        {
            "valid": bool,
            "assembly": {},         # 装配体数据结构
            "code": str,            # 生成的 build123d 代码
            "alignment": [...],     # 对齐变换矩阵
            "constraint_check": {}  # 约束检查结果
        }
    """
    # 1. 检查装配约束
    constraint_result = check_assembly_constraints(constraints)

    # 2. 构建装配体数据
    assembly = build_assembly_structure(parts, constraints)

    # 3. 求解对齐
    all_transforms = []
    for c in constraints:
        part_a = c.get("part_a", "")
        part_b = c.get("part_b", "")
        rules = get_alignment_rules(part_a, part_b)
        if rules:
            transforms = solve_alignment(parts, rules)
            all_transforms.extend(transforms)

    # 4. 生成代码
    code = generate_assembly_code(assembly)

    return {
        "valid": constraint_result["valid"],
        "assembly": assembly,
        "code": code,
        "alignment": all_transforms,
        "constraint_check": constraint_result,
    }
