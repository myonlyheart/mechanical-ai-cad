"""机械依赖推理引擎。

功能：
- 给定一个零件，推断所有依赖零件
- 自动选择匹配的组件
- 生成"为什么"解释链
- 输出完整的零件依赖图 + BOM + 校验结果
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .dependency_rules import (
    DEPENDENCY_RULES,
    DependencyRule,
    get_rules_for_source,
    get_rules_for_target,
    get_dependency_chain,
    validate_dependency,
)


@dataclass
class ReasoningStep:
    """推理步骤。"""
    step: int
    action: str                     # "auto_select", "validate", "propagate"
    source_type: str
    target_type: str
    reason: str
    params: dict[str, Any] = field(default_factory=dict)
    ok: bool = True
    details: str = ""


@dataclass
class DependencyNode:
    """依赖图中的零件节点。"""
    part_type: str
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)   # 依赖的零件名
    dependents: list[str] = field(default_factory=list)     # 被哪些零件依赖


@dataclass
class ReasoningResult:
    """推理结果。"""
    source_part: dict[str, Any]
    dependency_nodes: list[DependencyNode] = field(default_factory=list)
    reasoning_steps: list[ReasoningStep] = field(default_factory=list)
    auto_selected_parts: list[dict[str, Any]] = field(default_factory=list)
    validation_results: list[tuple[str, bool, str]] = field(default_factory=list)
    bom_items: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_part": self.source_part,
            "dependency_nodes": [
                {"part_type": n.part_type, "name": n.name, "params": n.params,
                 "dependencies": n.dependencies, "dependents": n.dependents}
                for n in self.dependency_nodes
            ],
            "reasoning_steps": [
                {"step": s.step, "action": s.action, "source": s.source_type,
                 "target": s.target_type, "reason": s.reason, "ok": s.ok,
                 "details": s.details, "params": s.params}
                for s in self.reasoning_steps
            ],
            "auto_selected_parts": self.auto_selected_parts,
            "validation_results": [
                {"rule": r, "ok": ok, "message": msg}
                for r, ok, msg in self.validation_results
            ],
            "bom_items": self.bom_items,
        }


class MechanicalReasoningEngine:
    """机械依赖推理引擎。

    使用规则驱动的方式推断零件依赖关系，自动选择匹配组件。
    """

    def __init__(self):
        self.rules = DEPENDENCY_RULES
        self._step_counter = 0

    def reason(self, part_type: str, params: dict[str, Any]) -> ReasoningResult:
        """对一个零件进行完整的依赖推理。

        1. 识别依赖规则
        2. 自动选择匹配组件
        3. 校验依赖关系
        4. 推导参数传播
        """
        self._step_counter = 0
        result = ReasoningResult(
            source_part={"part_type": part_type, "name": params.get("name", part_type), "params": params}
        )

        # 添加源节点
        source_node = DependencyNode(
            part_type=part_type,
            name=params.get("name", part_type),
            params=params,
        )
        result.dependency_nodes.append(source_node)

        # 获取依赖链
        chain = get_dependency_chain(part_type)
        if not chain:
            self._add_step(result, "info", part_type, "", f"零件类型 {part_type} 无已知依赖关系")
            return result

        # 处理每条规则
        processed_types: set[str] = set()
        self._process_dependencies(part_type, params, result, processed_types)

        # 生成 BOM 项
        self._generate_bom_items(result)

        return result

    def _process_dependencies(
        self,
        part_type: str,
        params: dict[str, Any],
        result: ReasoningResult,
        processed: set[str],
        depth: int = 0,
    ):
        """递归处理依赖关系。"""
        if depth > 5 or part_type in processed:
            return
        processed.add(part_type)

        # 作为 source 的规则：我依赖谁
        for rule in get_rules_for_source(part_type):
            self._apply_rule(rule, params, result, processed, depth, is_source=True)

        # 作为 target 的规则：谁依赖我
        for rule in get_rules_for_target(part_type):
            self._apply_rule(rule, params, result, processed, depth, is_source=False)

    def _apply_rule(
        self,
        rule: DependencyRule,
        params: dict[str, Any],
        result: ReasoningResult,
        processed: set[str],
        depth: int,
        is_source: bool,
    ):
        """应用一条依赖规则。"""
        if is_source:
            source_type, target_type = rule.source_type, rule.target_type
            source_params = params
        else:
            source_type, target_type = rule.target_type, rule.source_type
            source_params = params

        # 尝试自动选择
        auto_fn = rule.auto_select_fn if is_source else None
        if auto_fn:
            self._step_counter += 1
            selected = auto_fn(params)
            if selected:
                target_params = selected.get("params", selected)
                target_name = selected.get("name", target_type)

                # 添加推理步骤
                step = ReasoningStep(
                    step=self._step_counter,
                    action="auto_select",
                    source_type=source_type,
                    target_type=target_type,
                    reason=rule.reason,
                    params=target_params,
                    details=selected.get("reason", ""),
                )
                result.reasoning_steps.append(step)

                # 添加自动选择的零件
                part_entry = {
                    "part_type": target_type,
                    "name": target_name,
                    "params": target_params,
                    "reason": selected.get("reason", rule.reason),
                }
                result.auto_selected_parts.append(part_entry)

                # 添加依赖节点
                node = DependencyNode(
                    part_type=target_type,
                    name=target_name,
                    params=target_params,
                    dependencies=[params.get("name", source_type)],
                )
                result.dependency_nodes.append(node)

                # 更新源节点的 dependents
                for n in result.dependency_nodes:
                    if n.part_type == source_type and n.name == params.get("name", source_type):
                        n.dependents.append(target_name)

                # 递归处理下一层依赖
                self._process_dependencies(target_type, target_params, result, processed, depth + 1)

        # 校验已有零件
        if rule.constraint_fn:
            self._step_counter += 1
            if is_source:
                ok, msg = rule.constraint_fn(params, {})
            else:
                ok, msg = rule.constraint_fn({}, params)

            result.validation_results.append((rule.name, ok, msg))
            result.reasoning_steps.append(ReasoningStep(
                step=self._step_counter,
                action="validate",
                source_type=source_type,
                target_type=target_type,
                reason=rule.reason,
                ok=ok,
                details=msg,
            ))

    def _add_step(self, result: ReasoningResult, action: str, source: str, target: str, reason: str):
        self._step_counter += 1
        result.reasoning_steps.append(ReasoningStep(
            step=self._step_counter,
            action=action,
            source_type=source,
            target_type=target,
            reason=reason,
        ))

    def _generate_bom_items(self, result: ReasoningResult):
        """从依赖节点生成 BOM 项。"""
        for node in result.dependency_nodes:
            result.bom_items.append({
                "part_number": "",
                "part_name": node.name,
                "part_type": node.part_type,
                "material": node.params.get("material", "PLA"),
                "quantity": 1,
                "reason": f"{'源零件' if node.dependencies == [] else '依赖于 ' + ', '.join(node.dependencies)}",
            })


# ============================================================
# 快捷函数
# ============================================================

def reason_part(part_type: str, params: dict[str, Any]) -> dict[str, Any]:
    """对单个零件进行依赖推理。"""
    engine = MechanicalReasoningEngine()
    result = engine.reason(part_type, params)
    return result.to_dict()


def reason_assembly(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """对多个零件的装配体进行依赖推理。"""
    engine = MechanicalReasoningEngine()

    all_nodes: dict[str, DependencyNode] = {}
    all_steps: list[ReasoningStep] = []
    all_validations: list[tuple[str, bool, str]] = []

    for part in parts:
        part_type = part.get("part_type", "unknown")
        params = part.get("params", {})
        params["name"] = part.get("name", part_type)

        result = engine.reason(part_type, params)

        # 合并节点（去重）
        for node in result.dependency_nodes:
            key = f"{node.part_type}:{node.name}"
            if key not in all_nodes:
                all_nodes[key] = node

        all_steps.extend(result.reasoning_steps)
        all_validations.extend(result.validation_results)

    # 交叉校验：已知零件间的依赖
    part_list = list(all_nodes.values())
    for i, node_a in enumerate(part_list):
        for node_b in part_list[i + 1:]:
            ok, msg = validate_dependency(
                node_a.part_type, node_a.params,
                node_b.part_type, node_b.params,
            )
            if not ok:
                all_validations.append((f"{node_a.name}↔{node_b.name}", ok, msg))

    return {
        "parts_count": len(parts),
        "dependency_nodes": len(all_nodes),
        "reasoning_steps_count": len(all_steps),
        "reasoning_steps": [
            {"step": s.step, "action": s.action, "source": s.source_type,
             "target": s.target_type, "reason": s.reason, "ok": s.ok, "details": s.details}
            for s in all_steps
        ],
        "validation_results": [
            {"rule": r, "ok": ok, "message": msg}
            for r, ok, msg in all_validations
        ],
        "nodes": [
            {"part_type": n.part_type, "name": n.name, "params": n.params,
             "dependencies": n.dependencies, "dependents": n.dependents}
            for n in all_nodes.values()
        ],
    }
