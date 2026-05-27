"""API request/response models."""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class GenerateRequest(BaseModel):
    prompt: str
    project_id: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    part_type: Optional[str] = None


class GenerateResponse(BaseModel):
    id: int
    stl_url: str
    step_url: str = ""
    preview_url: str = ""
    code: str = ""
    parameters: Dict[str, Any] = {}
    part_type: str = ""
    status: str = "completed"


class ParamUpdateRequest(BaseModel):
    generation_id: int
    parameters: Dict[str, Any]


class HistoryItem(BaseModel):
    id: int
    prompt: str
    part_type: str
    parameters: Dict[str, Any]
    stl_url: str = ""
    created_at: str = ""
    status: str = ""


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int


# ============================================================
# 约束检查
# ============================================================

class ConstraintCheckRequest(BaseModel):
    part_type: str
    params: Dict[str, Any] = {}


class ConstraintCheckResponse(BaseModel):
    valid: bool
    original_params: Dict[str, Any] = {}
    fixed_params: Dict[str, Any] = {}
    issues: list[Dict[str, Any]] = []
    fixes_applied: list[str] = []


# ============================================================
# 多方案生成
# ============================================================

class DesignGenerateRequest(BaseModel):
    part_type: str
    base_params: Dict[str, Any] = {}
    requirements: Dict[str, Any] = {}


class DesignVariant(BaseModel):
    design_id: str
    name: str
    description: str
    params: Dict[str, Any] = {}
    performance: Dict[str, str] = {}
    constraint_check: Dict[str, Any] = {}


class DesignGenerateResponse(BaseModel):
    part_type: str
    designs: list[Dict[str, Any]] = []
    variants: list[DesignVariant] = []
    comparison: list[Dict[str, Any]] = []
    recommendation: str = ""


# ============================================================
# 自动装配
# ============================================================

class AssemblyBuildRequest(BaseModel):
    parts: list[Dict[str, Any]] = []
    constraints: list[Dict[str, Any]] = []


class AssemblyBuildResponse(BaseModel):
    valid: bool
    assembly: Dict[str, Any] = {}
    code: str = ""
    alignment: list[Dict[str, Any]] = []
    constraint_check: Dict[str, Any] = {}
