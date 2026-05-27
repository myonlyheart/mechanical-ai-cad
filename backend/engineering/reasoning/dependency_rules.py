"""机械依赖知识库 - 定义零件间的工程约束规则。

规则格式：DependencyRule
- source_type: 源零件类型
- target_type: 目标零件类型
- param_mapping: 源参数→目标参数映射
- constraint_fn: 校验函数，返回 (ok, message)
- auto_select_fn: 自动选择函数，根据源参数返回目标零件参数
- reason: 为什么存在此依赖（给用户的解释）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class DependencyRule:
    """零件间依赖规则。"""
    name: str
    source_type: str
    target_type: str
    param_mapping: dict[str, str]          # source_param -> target_param
    reason: str                            # 为什么需要这个依赖
    constraint_fn: Optional[Callable[[dict, dict], tuple[bool, str]]] = None
    auto_select_fn: Optional[Callable[[dict], dict]] = None


# ============================================================
# 轴 ↔ 轴承
# ============================================================

def _shaft_bearing_constraint(shaft_params: dict, bearing_params: dict) -> tuple[bool, str]:
    """轴直径必须匹配轴承内径。"""
    shaft_d = shaft_params.get("diameter", 8)
    bearing_id = bearing_params.get("inner_diameter", 8)
    if abs(shaft_d - bearing_id) < 0.01:
        return True, f"轴径 {shaft_d}mm 匹配轴承内径 {bearing_id}mm"
    return False, f"轴径 {shaft_d}mm ≠ 轴承内径 {bearing_id}mm（应为过盈或过渡配合）"


def _shaft_bearing_auto_select(shaft_params: dict) -> dict:
    """根据轴直径自动选择轴承。"""
    from ...components.bearings.bearing_generator import BEARING_SERIES_DIMS
    shaft_d = shaft_params.get("diameter", 8)
    # 查找内径匹配的轴承
    for name, dims in BEARING_SERIES_DIMS.items():
        if dims.get("id", 0) == shaft_d:
            return {
                "part_type": "bearing",
                "name": name,
                "params": {"series": name, **dims},
                "reason": f"轴径 {shaft_d}mm 匹配 {name} 轴承内径",
            }
    return {"reason": f"未找到内径 {shaft_d}mm 的标准轴承"}


# ============================================================
# 轴 ↔ 齿轮
# ============================================================

def _shaft_gear_constraint(shaft_params: dict, gear_params: dict) -> tuple[bool, str]:
    """齿轮孔径必须匹配轴径。"""
    shaft_d = shaft_params.get("diameter", 8)
    gear_bore = gear_params.get("bore_diameter", 8)
    if abs(shaft_d - gear_bore) < 0.01:
        return True, f"轴径 {shaft_d}mm 匹配齿轮孔径 {gear_bore}mm"
    return False, f"轴径 {shaft_d}mm ≠ 齿轮孔径 {gear_bore}mm"


def _shaft_gear_auto_select(shaft_params: dict) -> dict:
    """根据轴径设置齿轮孔径。"""
    shaft_d = shaft_params.get("diameter", 8)
    return {
        "bore_diameter": shaft_d,
        "reason": f"齿轮孔径设为轴径 {shaft_d}mm（配合 H7/g6）",
    }


# ============================================================
# 轴 ↔ 联轴器
# ============================================================

def _shaft_coupling_constraint(shaft_params: dict, coupling_params: dict) -> tuple[bool, str]:
    """联轴器孔径必须匹配轴径。"""
    shaft_d = shaft_params.get("diameter", 8)
    coupling_bore = coupling_params.get("bore_diameter", 8)
    if abs(shaft_d - coupling_bore) < 0.01:
        return True, f"轴径 {shaft_d}mm 匹配联轴器孔径 {coupling_bore}mm"
    return False, f"轴径 {shaft_d}mm ≠ 联轴器孔径 {coupling_bore}mm"


# ============================================================
# 齿轮 ↔ 齿轮（啮合）
# ============================================================

def _gear_gear_constraint(gear_a: dict, gear_b: dict) -> tuple[bool, str]:
    """啮合齿轮的模数必须相同。"""
    mod_a = gear_a.get("module", 2)
    mod_b = gear_b.get("module", 2)
    if abs(mod_a - mod_b) < 0.01:
        return True, f"齿轮模数一致: {mod_a}"
    return False, f"齿轮A模数 {mod_a} ≠ 齿轮B模数 {mod_b}（啮合齿轮模数必须相同）"


# ============================================================
# 电机 ↔ 安装座
# ============================================================

def _motor_mount_constraint(motor_params: dict, mount_params: dict) -> tuple[bool, str]:
    """安装座孔距必须匹配电机法兰孔距。"""
    motor_holes = motor_params.get("mount_hole_spacing", 31.0)
    mount_holes = mount_params.get("mount_hole_spacing", 31.0)
    if abs(motor_holes - mount_holes) < 0.5:
        return True, f"安装孔距匹配: {motor_holes}mm"
    return False, f"电机孔距 {motor_holes}mm ≠ 安装座孔距 {mount_holes}mm"


def _motor_mount_auto_select(motor_params: dict) -> dict:
    """根据电机类型选择安装座。"""
    from ...components.motors import get_mount_params
    motor_name = motor_params.get("motor_name", motor_params.get("name", "NEMA17"))
    mount = get_mount_params(motor_name)
    return {
        "part_type": "motor_mount",
        "name": f"{motor_name} Mount",
        "params": mount,
        "reason": f"根据 {motor_name} 电机法兰尺寸选择安装座",
    }


# ============================================================
# 螺栓 ↔ 孔
# ============================================================

def _bolt_hole_constraint(bolt_params: dict, hole_params: dict) -> tuple[bool, str]:
    """螺栓直径必须能穿过孔。"""
    bolt_d = bolt_params.get("diameter", 6)
    hole_d = hole_params.get("diameter", 7)
    if bolt_d < hole_d:
        return True, f"螺栓 M{bolt_d} 可穿过 Φ{hole_d}mm 孔（间隙 {hole_d - bolt_d:.1f}mm）"
    return False, f"螺栓 M{bolt_d} 无法穿过 Φ{hole_d}mm 孔"


# ============================================================
# 丝杆 ↔ 螺母
# ============================================================

def _screw_nut_constraint(screw_params: dict, nut_params: dict) -> tuple[bool, str]:
    """丝杆直径和螺距必须匹配螺母。"""
    s_d = screw_params.get("diameter", 8)
    n_d = nut_params.get("diameter", 8)
    if abs(s_d - n_d) < 0.01:
        return True, f"丝杆直径 {s_d}mm 匹配螺母"
    return False, f"丝杆直径 {s_d}mm ≠ 螺母配合直径 {n_d}mm"


# ============================================================
# 轴承 ↔ 轴承座
# ============================================================

def _bearing_housing_constraint(bearing_params: dict, housing_params: dict) -> tuple[bool, str]:
    """轴承外径必须匹配轴承座孔。"""
    bearing_od = bearing_params.get("outer_diameter", 22)
    housing_id = housing_params.get("inner_diameter", 22)
    if abs(bearing_od - housing_id) < 0.01:
        return True, f"轴承外径 {bearing_od}mm 匹配轴承座孔 Φ{housing_id}mm"
    return False, f"轴承外径 {bearing_od}mm ≠ 轴承座孔 Φ{housing_id}mm"


# ============================================================
# 规则注册表
# ============================================================

DEPENDENCY_RULES: list[DependencyRule] = [
    DependencyRule(
        name="shaft-bearing",
        source_type="shaft",
        target_type="bearing",
        param_mapping={"diameter": "inner_diameter"},
        reason="轴通过轴承支撑旋转，轴径必须与轴承内径配合（H7/g6 过渡配合）",
        constraint_fn=_shaft_bearing_constraint,
        auto_select_fn=_shaft_bearing_auto_select,
    ),
    DependencyRule(
        name="shaft-gear",
        source_type="shaft",
        target_type="gear",
        param_mapping={"diameter": "bore_diameter"},
        reason="齿轮安装在轴上，齿轮孔径必须与轴径配合",
        constraint_fn=_shaft_gear_constraint,
        auto_select_fn=_shaft_gear_auto_select,
    ),
    DependencyRule(
        name="shaft-coupling",
        source_type="shaft",
        target_type="coupling",
        param_mapping={"diameter": "bore_diameter"},
        reason="联轴器连接两根轴，孔径必须与轴径配合",
        constraint_fn=_shaft_coupling_constraint,
    ),
    DependencyRule(
        name="gear-gear-mesh",
        source_type="gear",
        target_type="gear",
        param_mapping={"module": "module"},
        reason="啮合齿轮的模数必须相同，否则无法正确传动",
        constraint_fn=_gear_gear_constraint,
    ),
    DependencyRule(
        name="motor-mount",
        source_type="motor",
        target_type="motor_mount",
        param_mapping={"mount_hole_spacing": "mount_hole_spacing"},
        reason="电机安装座的孔距必须与电机法兰孔距一致",
        constraint_fn=_motor_mount_constraint,
        auto_select_fn=_motor_mount_auto_select,
    ),
    DependencyRule(
        name="bolt-hole",
        source_type="bolt",
        target_type="hole",
        param_mapping={"diameter": "bolt_diameter"},
        reason="螺栓必须能穿过安装孔（ISO 273 间隙配合）",
        constraint_fn=_bolt_hole_constraint,
    ),
    DependencyRule(
        name="bearing-housing",
        source_type="bearing",
        target_type="bearing_block",
        param_mapping={"outer_diameter": "inner_diameter"},
        reason="轴承外径必须与轴承座孔配合（H7/k6 过渡配合）",
        constraint_fn=_bearing_housing_constraint,
    ),
    DependencyRule(
        name="lead-screw-nut",
        source_type="lead_screw",
        target_type="nut",
        param_mapping={"diameter": "diameter"},
        reason="丝杆螺母必须与丝杆直径和螺距匹配",
        constraint_fn=_screw_nut_constraint,
    ),
]


# ============================================================
# 依赖链查询
# ============================================================

def get_rules_for_source(source_type: str) -> list[DependencyRule]:
    """获取指定源零件类型的所有依赖规则。"""
    return [r for r in DEPENDENCY_RULES if r.source_type == source_type]


def get_rules_for_target(target_type: str) -> list[DependencyRule]:
    """获取指定目标零件类型的所有依赖规则。"""
    return [r for r in DEPENDENCY_RULES if r.target_type == target_type]


def get_dependency_chain(part_type: str) -> list[DependencyRule]:
    """获取零件的完整依赖链（递归）。

    例如：gear → [gear-shaft, shaft-bearing, shaft-coupling]
    """
    chain = []
    visited = set()
    stack = [part_type]

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)

        for rule in DEPENDENCY_RULES:
            if rule.source_type == current:
                chain.append(rule)
                stack.append(rule.target_type)
            elif rule.target_type == current:
                chain.append(rule)
                stack.append(rule.source_type)

    return chain


def validate_dependency(source_type: str, source_params: dict,
                        target_type: str, target_params: dict) -> tuple[bool, str]:
    """校验两个零件间的依赖关系。"""
    for rule in DEPENDENCY_RULES:
        if (rule.source_type == source_type and rule.target_type == target_type):
            if rule.constraint_fn:
                return rule.constraint_fn(source_params, target_params)
        elif (rule.source_type == target_type and rule.target_type == source_type):
            if rule.constraint_fn:
                return rule.constraint_fn(target_params, source_params)
    return True, f"无已知依赖规则: {source_type} - {target_type}"
