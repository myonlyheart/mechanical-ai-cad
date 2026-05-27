"""几何校验 - 检测几何模型的有效性。

检测项：
- self intersection（自相交）
- zero thickness（零厚度）
- non manifold（非流形）
- invalid topology（无效拓扑）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ValidationSeverity(str, Enum):
    """校验严重级别。"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """几何校验错误。"""
    code: str = ""
    message: str = ""
    severity: str = ValidationSeverity.ERROR
    fix_suggestion: str = ""
    location: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "fix_suggestion": self.fix_suggestion,
            "location": self.location,
        }


@dataclass
class GeometryValidationResult:
    """几何校验结果。"""
    valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    checks_performed: list[str] = field(default_factory=list)

    def add_error(self, code: str, message: str, fix: str = "") -> None:
        self.errors.append(ValidationError(code=code, message=message, severity="error", fix_suggestion=fix))
        self.valid = False

    def add_warning(self, code: str, message: str, fix: str = "") -> None:
        self.warnings.append(ValidationError(code=code, message=message, severity="warning", fix_suggestion=fix))

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "checks_performed": self.checks_performed,
        }


def check_self_intersection(geometry: Any) -> GeometryValidationResult:
    """检查自相交。"""
    result = GeometryValidationResult()
    result.checks_performed.append("self_intersection")

    if geometry is None:
        result.add_error("no_geometry", "几何对象为空，无法检查")
        return result

    # build123d 有 is_valid() 方法
    try:
        if hasattr(geometry, "is_valid") and not geometry.is_valid():
            result.add_error(
                "invalid_geometry", "几何体无效（可能包含自相交）",
                "检查并修复几何体的拓扑结构",
            )
    except Exception as e:
        result.add_warning("check_failed", f"自相交检查失败: {e}")

    return result


def check_zero_thickness(geometry: Any) -> GeometryValidationResult:
    """检查零厚度。"""
    result = GeometryValidationResult()
    result.checks_performed.append("zero_thickness")

    if geometry is None:
        return result

    try:
        if hasattr(geometry, "bounding_box"):
            bb = geometry.bounding_box()
            if hasattr(bb, "size"):
                size = bb.size
                # 检查三个维度是否都大于零
                if size.X < 0.01 or size.Y < 0.01 or size.Z < 0.01:
                    result.add_error(
                        "zero_thickness", "几何体在某个维度上厚度接近零",
                        "增加薄壁厚度或修复几何体",
                    )
    except Exception as e:
        result.add_warning("check_failed", f"零厚度检查失败: {e}")

    return result


def check_non_manifold(geometry: Any) -> GeometryValidationResult:
    """检查非流形边。"""
    result = GeometryValidationResult()
    result.checks_performed.append("non_manifold")

    if geometry is None:
        return result

    try:
        # build123d 的 Solid 有 is_manifold 属性（如果有）
        if hasattr(geometry, "is_manifold") and not geometry.is_manifold():
            result.add_error(
                "non_manifold_edge", "存在非流形边/顶点",
                "合并或分离共享边/顶点",
            )
    except Exception as e:
        result.add_warning("check_failed", f"非流形检查失败: {e}")

    return result


def check_topology(geometry: Any) -> GeometryValidationResult:
    """检查拓扑有效性。"""
    result = GeometryValidationResult()
    result.checks_performed.append("topology")

    if geometry is None:
        return result

    try:
        # 检查是否为封闭实体
        if hasattr(geometry, "is_closed") and not geometry.is_closed():
            result.add_error(
                "not_closed", "几何体不是封闭实体",
                "封闭所有开放面",
            )
    except Exception as e:
        result.add_warning("check_failed", f"拓扑检查失败: {e}")

    return result


def validate_geometry(geometry: Any) -> GeometryValidationResult:
    """完整几何校验。

    Args:
        geometry: build123d 几何对象

    Returns:
        GeometryValidationResult
    """
    results = [
        check_self_intersection(geometry),
        check_zero_thickness(geometry),
        check_non_manifold(geometry),
        check_topology(geometry),
    ]

    combined = GeometryValidationResult()
    for r in results:
        combined.errors.extend(r.errors)
        combined.warnings.extend(r.warnings)
        combined.checks_performed.extend(r.checks_performed)
        if not r.valid:
            combined.valid = False

    return combined
