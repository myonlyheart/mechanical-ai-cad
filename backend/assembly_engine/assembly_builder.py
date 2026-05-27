"""装配构建器 - 将多个零件组合成完整装配体"""

import json
from pathlib import Path
from typing import Optional

from ..core.models import Part, Assembly


def build_assembly_structure(parts: list[dict], constraints: list[dict]) -> dict:
    """构建装配体的数据结构

    Args:
        parts: 零件列表 [{"name": "motor", "part_type": "motor", "params": {...}}, ...]
        constraints: 装配约束列表 [{"type": "fixed_to", "part_a": "motor", "part_b": "bracket"}, ...]

    Returns:
        装配体描述字典
    """
    return {
        "parts": [
            {
                "name": p.get("name", f"part_{i}"),
                "part_type": p.get("part_type", "unknown"),
                "params": p.get("params", {}),
                "position": p.get("position", [0, 0, 0]),
            }
            for i, p in enumerate(parts)
        ],
        "constraints": constraints,
        "metadata": {
            "part_count": len(parts),
            "constraint_count": len(constraints),
        },
    }


def generate_assembly_code(assembly: dict) -> str:
    """生成装配体的 build123d Python 代码"""
    lines = [
        '"""自动生成的装配体代码"""',
        "from build123d import *",
        "from cad import *",
        "",
        "parts = {}",
        "",
    ]

    # 为每个零件生成构建代码
    for part in assembly.get("parts", []):
        name = part["name"]
        ptype = part.get("part_type", "")
        params = part.get("params", {})

        if ptype in ("motor", "nema17"):
            lines.append(f'# {name} - NEMA17 电机')
            lines.append(f'parts["{name}"] = {{')
            lines.append(f'    "type": "motor",')
            lines.append(f'    "mounting_hole_spacing": {params.get("mounting_hole_spacing", 31.0)},')
            lines.append(f'    "shaft_diameter": {params.get("shaft_diameter", 5.0)},')
            lines.append(f'}}')
        elif ptype == "bracket":
            lines.append(f'# {name} - 支架')
            lines.append(f'params_{name} = LBracketParams(**{json.dumps(params)})')
            lines.append(f'parts["{name}"] = LBracket(params_{name}).build()')
        elif ptype == "motor_mount":
            lines.append(f'# {name} - 电机支架')
            lines.append(f'params_{name} = NEMA17MountParams(**{json.dumps(params)})')
            lines.append(f'parts["{name}"] = NEMA17Mount(params_{name}).build()')
        elif ptype == "gear":
            lines.append(f'# {name} - 齿轮')
            lines.append(f'params_{name} = SpurGearParams(**{json.dumps(params)})')
            lines.append(f'parts["{name}"] = SpurGear(params_{name}).build()')
        else:
            lines.append(f'# {name} - {ptype}（未知类型，跳过）')

        lines.append("")

    # 装配关系
    lines.append("# 装配关系")
    lines.append("assembly = Compound(")
    for c in assembly.get("constraints", []):
        a = c.get("part_a", "")
        b = c.get("part_b", "")
        ctype = c.get("type", "")
        lines.append(f'    # {a} → {b} ({ctype})')
    lines.append("    children=list(parts.values())")
    lines.append(")")

    return "\n".join(lines)


def build_assembly_object(parts: list[dict], constraints: list[dict], name: str = "assembly") -> Assembly:
    """构建 Assembly 统一数据对象。

    Args:
        parts: 零件列表 [{"name": "motor", "part_type": "motor", "params": {...}}, ...]
        constraints: 装配约束列表
        name: 装配体名称

    Returns:
        Assembly 对象
    """
    assembly = Assembly(name=name, constraints=constraints)
    for i, p in enumerate(parts):
        part = Part(
            name=p.get("name", f"part_{i}"),
            part_type=p.get("part_type", "unknown"),
            parameters=p.get("params", {}),
            metadata={"position": p.get("position", [0, 0, 0])},
        )
        assembly.add_part(part)
    return assembly
