"""API request/response models."""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class GenerateRequest(BaseModel):
    prompt: str
    project_id: Optional[int] = None


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
