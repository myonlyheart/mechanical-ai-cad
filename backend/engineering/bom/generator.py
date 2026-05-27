"""BOM (Bill of Materials) 物料清单生成器。

功能：
- 自动零件编号
- 去重（相同参数的零件合并）
- 数量统计
- 材料推断
- 输出 CSV / Excel / PDF
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ...core.models import Part, Assembly


# ============================================================
# BOM 数据结构
# ============================================================

@dataclass
class BOMItem:
    """BOM 行项。"""
    part_number: str = ""
    part_name: str = ""
    material: str = "PLA"
    quantity: int = 1
    weight_g: float = 0.0
    manufacturing_method: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "part_number": self.part_number,
            "part_name": self.part_name,
            "material": self.material,
            "quantity": self.quantity,
            "weight_g": round(self.weight_g, 1),
            "manufacturing_method": self.manufacturing_method,
            "notes": self.notes,
        }


@dataclass
class BOM:
    """物料清单。"""
    title: str = "Bill of Materials"
    items: list[BOMItem] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_parts(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def unique_parts(self) -> int:
        return len(self.items)

    @property
    def total_weight_g(self) -> float:
        return sum(item.weight_g * item.quantity for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "total_parts": self.total_parts,
            "unique_parts": self.unique_parts,
            "total_weight_g": round(self.total_weight_g, 1),
            "items": [item.to_dict() for item in self.items],
            "metadata": self.metadata,
        }


# ============================================================
# 零件指纹（用于去重）
# ============================================================

def _part_fingerprint(part_type: str, params: dict[str, Any]) -> str:
    """生成零件指纹用于去重。"""
    key = f"{part_type}:{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(key.encode()).hexdigest()[:8]


def _generate_part_number(index: int, part_type: str) -> str:
    """生成零件编号。"""
    prefix_map = {
        "bracket": "BRK",
        "lbracket": "BRK",
        "tbracket": "BRK",
        "gear": "GAR",
        "spurgear": "GAR",
        "motor_mount": "MTM",
        "nema17mount": "MTM",
        "motor": "MOT",
        "shaft": "SHF",
        "bearing": "BRG",
    }
    prefix = prefix_map.get(part_type.lower(), "PRT")
    return f"{prefix}-{index:03d}"


def _infer_material(params: dict[str, Any]) -> str:
    """推断材料。"""
    return params.get("material", "PLA")


def _estimate_weight(params: dict[str, Any], part_type: str) -> float:
    """估算重量（简化版）。"""
    density = {
        "PLA": 1.24, "ABS": 1.04, "PETG": 1.27,
        "TPU": 1.2, "Nylon": 1.14, "steel": 7.85,
    }
    mat = params.get("material", "PLA")
    d = density.get(mat, 1.24)

    # 简化体积估算
    thickness = params.get("thickness", params.get("base_thickness", 5))
    length = params.get("length", params.get("base_length", 60))
    width = params.get("width", params.get("base_width", 40))
    height = params.get("height", params.get("mount_height", 40))

    volume_cm3 = (length * width * height) / 1000  # mm³ → cm³

    # 中空/晶格修正
    if params.get("hollow"):
        volume_cm3 *= 0.4
    elif params.get("lattice_fill"):
        volume_cm3 *= 0.25
    else:
        volume_cm3 *= 0.6  # 非实心修正

    return round(volume_cm3 * d, 1)


def _infer_manufacturing_method(params: dict[str, Any]) -> str:
    """推断制造方法。"""
    material = params.get("material", "PLA").upper()
    if material in ("PLA", "PETG", "ABS", "TPU", "NYLON"):
        return "3D打印 (FDM)"
    return "机加工"


# ============================================================
# BOM 生成
# ============================================================

def generate_bom_from_parts(
    parts: list[dict[str, Any]],
    title: str = "Bill of Materials",
) -> BOM:
    """从零件列表生成 BOM。

    Args:
        parts: [{"name": "xxx", "part_type": "bracket", "params": {...}}, ...]
        title: BOM 标题

    Returns:
        BOM 对象
    """
    # 按指纹去重
    fingerprint_map: dict[str, dict[str, Any]] = {}
    fingerprint_count: dict[str, int] = defaultdict(int)

    for part in parts:
        part_type = part.get("part_type", "unknown")
        params = part.get("params", {})
        fp = _part_fingerprint(part_type, params)

        if fp not in fingerprint_map:
            fingerprint_map[fp] = part
        fingerprint_count[fp] += 1

    # 生成 BOM 项
    items: list[BOMItem] = []
    for idx, (fp, part) in enumerate(fingerprint_map.items(), start=1):
        part_type = part.get("part_type", "unknown")
        params = part.get("params", {})
        name = part.get("name", f"{part_type}_{idx}")

        items.append(BOMItem(
            part_number=_generate_part_number(idx, part_type),
            part_name=name,
            material=_infer_material(params),
            quantity=fingerprint_count[fp],
            weight_g=_estimate_weight(params, part_type),
            manufacturing_method=_infer_manufacturing_method(params),
            parameters=params,
        ))

    return BOM(title=title, items=items)


def generate_bom_from_assembly(assembly: Assembly) -> BOM:
    """从 Assembly 对象生成 BOM。"""
    parts = [p.to_dict() for p in assembly.children]
    return generate_bom_from_parts(parts, title=f"BOM - {assembly.name}")


# ============================================================
# 输出格式
# ============================================================

def bom_to_csv(bom: BOM) -> str:
    """导出为 CSV 字符串。"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Part Number", "Part Name", "Material", "Quantity", "Weight (g)", "Manufacturing Method", "Notes"])
    for item in bom.items:
        writer.writerow([
            item.part_number, item.part_name, item.material,
            item.quantity, f"{item.weight_g:.1f}", item.manufacturing_method, item.notes,
        ])
    # 汇总行
    writer.writerow([])
    writer.writerow(["", "Total", "", bom.total_parts, f"{bom.total_weight_g:.1f}", "", ""])
    return output.getvalue()


def bom_to_dict_list(bom: BOM) -> list[dict[str, Any]]:
    """导出为字典列表（JSON 友好）。"""
    return [item.to_dict() for item in bom.items]


def save_bom_csv(bom: BOM, filepath: str) -> str:
    """保存 BOM 为 CSV 文件。"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(bom_to_csv(bom), encoding="utf-8-sig")
    return str(path)


def save_bom_json(bom: BOM, filepath: str) -> str:
    """保存 BOM 为 JSON 文件。"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bom.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
