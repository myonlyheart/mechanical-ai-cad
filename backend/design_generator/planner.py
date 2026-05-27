"""设计策略规划器 - 从用户需求生成多个设计方向"""

import json
import os
from typing import Optional

# 设计策略模板库
DESIGN_STRATEGIES = {
    "bracket": [
        {
            "id": "solid",
            "name": "实心加强型",
            "description": "全实体结构，最大强度",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {},
        },
        {
            "id": "ribbed",
            "name": "肋板加强型",
            "description": "主体薄壁 + 加强筋，兼顾强度和轻量",
            "weight_factor": 0.6,
            "strength_factor": 0.85,
            "time_factor": 0.8,
            "params_override": {"add_ribs": True},
        },
        {
            "id": "lightweight_lattice",
            "name": "轻量化晶格型",
            "description": "内部蜂窝/晶格填充，极轻重量",
            "weight_factor": 0.3,
            "strength_factor": 0.5,
            "time_factor": 1.5,
            "params_override": {"lattice_fill": True},
        },
        {
            "id": "hollow_shell",
            "name": "中空壳体型",
            "description": "中空结构 + 厚壁，适合大尺寸件",
            "weight_factor": 0.45,
            "strength_factor": 0.7,
            "time_factor": 0.9,
            "params_override": {"hollow": True, "shell_thickness": 2.0},
        },
    ],
    "motor_mount": [
        {
            "id": "standard_l",
            "name": "标准 L 型",
            "description": "经典 L 型支架，水平 + 垂直安装面",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {},
        },
        {
            "id": "compact",
            "name": "紧凑型",
            "description": "缩小基座尺寸，节省空间",
            "weight_factor": 0.7,
            "strength_factor": 0.8,
            "time_factor": 0.7,
            "params_override": {"base_length": 50, "base_width": 50},
        },
        {
            "id": "reinforced",
            "name": "加强型（加肋）",
            "description": "在转角处添加三角肋板，提升刚性",
            "weight_factor": 1.15,
            "strength_factor": 1.3,
            "time_factor": 1.1,
            "params_override": {"add_gussets": True},
        },
        {
            "id": "adjustable",
            "name": "可调高度型",
            "description": "多排安装孔，高度可调节",
            "weight_factor": 1.1,
            "strength_factor": 0.95,
            "time_factor": 1.2,
            "params_override": {"adjustable_height": True},
        },
    ],
    "gear": [
        {
            "id": "standard_spur",
            "name": "标准直齿轮",
            "description": "经典渐开线直齿轮",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {},
        },
        {
            "id": "lightweight_spur",
            "name": "轻量化直齿轮",
            "description": "辐板结构减重",
            "weight_factor": 0.6,
            "strength_factor": 0.85,
            "time_factor": 1.1,
            "params_override": {"web_style": "spoked"},
        },
        {
            "id": "wide_face",
            "name": "宽面齿轮",
            "description": "增加齿面宽度，提高扭矩承载",
            "weight_factor": 1.3,
            "strength_factor": 1.4,
            "time_factor": 1.2,
            "params_override": {"width_factor": 1.5},
        },
    ],
    "bearing_block": [
        {
            "id": "standard_bearing",
            "name": "标准型",
            "description": "标准轴承座，通用安装",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {},
        },
        {
            "id": "lightweight_bearing",
            "name": "轻量化",
            "description": "缩小基座，减轻重量",
            "weight_factor": 0.65,
            "strength_factor": 0.8,
            "time_factor": 0.8,
            "params_override": {"base_length": 45, "base_width": 30},
        },
        {
            "id": "reinforced_bearing",
            "name": "加强型",
            "description": "加厚基座，提高刚性",
            "weight_factor": 1.3,
            "strength_factor": 1.4,
            "time_factor": 1.1,
            "params_override": {"base_thickness": 12, "height": 35},
        },
        {
            "id": "flanged_bearing",
            "name": "带法兰型",
            "description": "侧面法兰固定，适合受限空间",
            "weight_factor": 1.1,
            "strength_factor": 1.1,
            "time_factor": 1.2,
            "params_override": {},
        },
    ],
    "flange": [
        {
            "id": "standard_flange",
            "name": "标准型",
            "description": "标准圆法兰，通用连接",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {},
        },
        {
            "id": "lightweight_flange",
            "name": "轻量化",
            "description": "减薄厚度，轻载应用",
            "weight_factor": 0.6,
            "strength_factor": 0.7,
            "time_factor": 0.8,
            "params_override": {"thickness": 5},
        },
        {
            "id": "heavy_flange",
            "name": "重型型",
            "description": "加厚加大，高压应用",
            "weight_factor": 1.5,
            "strength_factor": 1.6,
            "time_factor": 1.3,
            "params_override": {"thickness": 12, "outer_diameter": 100},
        },
        {
            "id": "raised_face",
            "name": "凸面型",
            "description": "带凸台密封面",
            "weight_factor": 1.15,
            "strength_factor": 1.1,
            "time_factor": 1.1,
            "params_override": {},
        },
    ],
    "coupling": [
        {
            "id": "rigid_coupling",
            "name": "刚性型",
            "description": "刚性联轴器，高扭矩传递",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {},
        },
        {
            "id": "flexible_coupling",
            "name": "弹性型",
            "description": "更多弹性槽，补偿偏差",
            "weight_factor": 0.9,
            "strength_factor": 0.85,
            "time_factor": 1.2,
            "params_override": {"slit_count": 8},
        },
        {
            "id": "compact_coupling",
            "name": "紧凑型",
            "description": "缩短长度，节省空间",
            "weight_factor": 0.7,
            "strength_factor": 0.8,
            "time_factor": 0.8,
            "params_override": {"length": 25},
        },
        {
            "id": "clamping_coupling",
            "name": "夹紧型",
            "description": "外径加大，夹紧固定",
            "weight_factor": 1.2,
            "strength_factor": 1.2,
            "time_factor": 1.1,
            "params_override": {"outer_diameter": 38},
        },
    ],
    "shaft_sleeve": [
        {
            "id": "smooth_sleeve",
            "name": "光滑型",
            "description": "光面轴套，标准应用",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {"flange_thickness": 0},
        },
        {
            "id": "flanged_sleeve",
            "name": "带凸缘型",
            "description": "端面凸缘定位",
            "weight_factor": 1.2,
            "strength_factor": 1.1,
            "time_factor": 1.1,
            "params_override": {},
        },
        {
            "id": "keyed_sleeve",
            "name": "带键槽型",
            "description": "内孔键槽，防转动",
            "weight_factor": 1.0,
            "strength_factor": 0.95,
            "time_factor": 1.1,
            "params_override": {"keyway_width": 4, "keyway_depth": 2},
        },
        {
            "id": "grooved_sleeve",
            "name": "带油槽型",
            "description": "外圆油槽，润滑储油",
            "weight_factor": 0.95,
            "strength_factor": 0.9,
            "time_factor": 1.2,
            "params_override": {},
        },
    ],
    "bolt": [
        {
            "id": "hex_bolt",
            "name": "六角螺栓",
            "description": "标准六角头，通用紧固",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {"head_type": "hex"},
        },
        {
            "id": "socket_bolt",
            "name": "内六角螺钉",
            "description": "圆柱头内六角，沉头安装",
            "weight_factor": 0.9,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {"head_type": "socket"},
        },
        {
            "id": "flat_bolt",
            "name": "沉头螺钉",
            "description": "平头沉入安装面",
            "weight_factor": 0.85,
            "strength_factor": 0.95,
            "time_factor": 1.0,
            "params_override": {"head_type": "flat"},
        },
    ],
    "nut": [
        {
            "id": "hex_nut",
            "name": "六角螺母",
            "description": "标准六角螺母",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {"nut_type": "hex"},
        },
        {
            "id": "flange_nut",
            "name": "法兰螺母",
            "description": "带法兰面，增大承压面积",
            "weight_factor": 1.2,
            "strength_factor": 1.1,
            "time_factor": 1.0,
            "params_override": {"nut_type": "flange"},
        },
        {
            "id": "nylock_nut",
            "name": "锁紧螺母",
            "description": "尼龙嵌件防松",
            "weight_factor": 1.1,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {"nut_type": "nylock"},
        },
    ],
    "shaft": [
        {
            "id": "round_shaft",
            "name": "光轴",
            "description": "简单圆柱轴，通用传动",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {"shaft_type": "round"},
        },
        {
            "id": "keyed_shaft",
            "name": "键槽轴",
            "description": "带键槽，齿轮/联轴器防转",
            "weight_factor": 0.95,
            "strength_factor": 0.9,
            "time_factor": 1.1,
            "params_override": {"shaft_type": "keyed"},
        },
        {
            "id": "stepped_shaft",
            "name": "台阶轴",
            "description": "多段不同直径，轴肩定位",
            "weight_factor": 1.1,
            "strength_factor": 1.2,
            "time_factor": 1.2,
            "params_override": {"shaft_type": "stepped", "steps": [(12, 30), (8, 60), (6, 30)]},
        },
        {
            "id": "threaded_shaft",
            "name": "螺纹轴",
            "description": "端部螺纹，螺母固定",
            "weight_factor": 0.95,
            "strength_factor": 0.95,
            "time_factor": 1.1,
            "params_override": {"shaft_type": "threaded", "thread_length": 20},
        },
    ],
    "washer": [
        {
            "id": "flat_washer",
            "name": "平垫片",
            "description": "标准平垫，分散压力",
            "weight_factor": 1.0,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {"washer_type": "flat"},
        },
        {
            "id": "spring_washer",
            "name": "弹簧垫片",
            "description": "开口弹簧垫，防松",
            "weight_factor": 0.8,
            "strength_factor": 0.9,
            "time_factor": 1.0,
            "params_override": {"washer_type": "spring"},
        },
        {
            "id": "lock_washer",
            "name": "锁紧垫片",
            "description": "内齿锁紧垫，防转动",
            "weight_factor": 0.9,
            "strength_factor": 1.0,
            "time_factor": 1.0,
            "params_override": {"washer_type": "lock"},
        },
    ],
}

# 载荷等级对应的系数
LOAD_MULTIPLIERS = {
    "light":  {"strength": 0.8, "weight": 0.9, "wall_min": 1.2},
    "medium": {"strength": 1.0, "weight": 1.0, "wall_min": 2.0},
    "heavy":  {"strength": 1.3, "weight": 1.2, "wall_min": 3.0},
}


def plan_designs(part_type: str, requirements: dict) -> list[dict]:
    """根据需求生成多个设计方案

    Args:
        part_type: 零件类型
        requirements: 需求描述，如 {"load": "light", "material": "PLA", ...}

    Returns:
        设计方案列表，每个方案包含参数建议和性能估算
    """
    strategies = DESIGN_STRATEGIES.get(part_type, [])
    if not strategies:
        return [{"id": "default", "name": "默认方案", "description": "未找到预设策略，使用默认参数", "weight_factor": 1.0, "strength_factor": 1.0, "time_factor": 1.0, "params_override": {}}]

    load = requirements.get("load", "medium")
    material = requirements.get("material", "PLA")
    multiplier = LOAD_MULTIPLIERS.get(load, LOAD_MULTIPLIERS["medium"])

    designs = []
    for strategy in strategies:
        design = {
            "design_id": strategy["id"],
            "name": strategy["name"],
            "description": strategy["description"],
            "estimated_weight": _estimate_weight(strategy["weight_factor"] * multiplier["weight"], material),
            "estimated_strength": _strength_label(strategy["strength_factor"] * multiplier["strength"]),
            "estimated_print_time": _estimate_time(strategy["time_factor"]),
            "params_override": strategy["params_override"],
        }
        designs.append(design)

    return designs


def _estimate_weight(factor: float, material: str) -> str:
    density = {"PLA": 1.24, "ABS": 1.04, "PETG": 1.27, "TPU": 1.2}.get(material, 1.2)
    if factor < 0.4:
        return "极轻"
    elif factor < 0.7:
        return "轻"
    elif factor < 1.0:
        return "中等"
    else:
        return "重"


def _strength_label(factor: float) -> str:
    if factor > 1.2:
        return "极高"
    elif factor > 0.9:
        return "高"
    elif factor > 0.6:
        return "中等"
    else:
        return "低"


def _estimate_time(factor: float) -> str:
    base_hours = 2.0
    hours = base_hours * factor
    if hours < 1:
        return f"{int(hours * 60)}分钟"
    elif hours < 3:
        return f"{hours:.1f}小时"
    else:
        return f"{hours:.0f}小时"
