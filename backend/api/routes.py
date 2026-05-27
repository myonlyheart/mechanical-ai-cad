"""API routes for the CAD platform."""

import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from .models import GenerateRequest, GenerateResponse, ParamUpdateRequest, HistoryItem, HistoryResponse
from ..database import get_db
from ..database.models import Generation
from ..prompts import PromptEngine
from ..cad import (
    LBracket, LBracketParams, TBracket, TBracketParams,
    SpurGear, SpurGearParams, NEMA17Mount, NEMA17MountParams,
    export_stl, export_step,
)

router = APIRouter()
prompt_engine = PromptEngine()
EXPORTS_DIR = Path(__file__).parent.parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


def generate_cad_code(part_type: str, params: dict) -> str:
    if part_type == "bracket":
        return f'''from build123d import *
from cad import LBracket, LBracketParams

params = LBracketParams(
    length={params.get("length", 80)},
    width={params.get("width", 40)},
    height={params.get("height", 60)},
    thickness={params.get("thickness", 5)},
    hole_diameter={params.get("hole_diameter", 6.5)},
    hole_count={params.get("hole_count", 4)},
)
bracket = LBracket(params)
part = bracket.build()
'''
    elif part_type == "gear":
        return f'''from build123d import *
from cad import SpurGear, SpurGearParams

params = SpurGearParams(
    module={params.get("module", 2)},
    teeth_count={params.get("teeth_count", 20)},
    width={params.get("width", 10)},
    bore_diameter={params.get("bore_diameter", 8)},
)
gear = SpurGear(params)
part = gear.build()
'''
    elif part_type == "motor_mount":
        return f'''from build123d import *
from cad import NEMA17Mount, NEMA17MountParams

params = NEMA17MountParams(
    base_length={params.get("base_length", 60)},
    base_width={params.get("base_width", 60)},
    base_thickness={params.get("base_thickness", 5)},
    mount_height={params.get("mount_height", 40)},
)
mount = NEMA17Mount(params)
part = mount.build()
'''
    return "# 不支持的零件类型"


def build_part(part_type: str, params: dict):
    if part_type == "bracket":
        p = LBracketParams(**{k: v for k, v in params.items() if hasattr(LBracketParams, k)})
        return LBracket(p).build()
    elif part_type == "gear":
        p = SpurGearParams(**{k: v for k, v in params.items() if hasattr(SpurGearParams, k)})
        return SpurGear(p).build()
    elif part_type == "motor_mount":
        p = NEMA17MountParams(**{k: v for k, v in params.items() if hasattr(NEMA17MountParams, k)})
        return NEMA17Mount(p).build()
    raise ValueError(f"不支持的零件类型: {part_type}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_model(request: GenerateRequest, db: Session = Depends(get_db)):
    # Support explicit params (from variant selection) or NLP parsing
    if request.parameters and request.part_type:
        part_type = request.part_type
        params = request.parameters
    else:
        parsed = prompt_engine.process(request.prompt)
        is_valid, msg = prompt_engine.validate_params(parsed)
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)
        part_type = parsed["type"]
        params = parsed["params"]

    gen = Generation(
        project_id=request.project_id,
        prompt=request.prompt,
        part_type=part_type,
        parameters=json.dumps(params),
        status="generating",
    )
    db.add(gen)
    db.commit()
    db.refresh(gen)

    try:
        part = build_part(part_type, params)
        stl_filename = f"model_{gen.id}"
        stl_path = export_stl(part, stl_filename)
        step_path = export_step(part, stl_filename)
        code = generate_cad_code(part_type, params)

        gen.stl_path = stl_path
        gen.step_path = step_path
        gen.cad_code = code
        gen.status = "completed"
        db.commit()

        return GenerateResponse(
            id=gen.id,
            stl_url=f"/exports/{stl_filename}.stl",
            step_url=f"/exports/{stl_filename}.step",
            code=code,
            parameters=params,
            part_type=part_type,
            status="completed",
        )
    except Exception as e:
        gen.status = "error"
        gen.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-params", response_model=GenerateResponse)
async def update_parameters(request: ParamUpdateRequest, db: Session = Depends(get_db)):
    gen = db.query(Generation).filter(Generation.id == request.generation_id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="未找到生成记录")

    params = request.parameters
    part_type = gen.part_type

    try:
        part = build_part(part_type, params)
        stl_filename = f"model_{gen.id}_v2"
        stl_path = export_stl(part, stl_filename)
        step_path = export_step(part, stl_filename)
        code = generate_cad_code(part_type, params)

        gen.parameters = json.dumps(params)
        gen.stl_path = stl_path
        gen.step_path = step_path
        gen.cad_code = code
        gen.status = "completed"
        db.commit()

        return GenerateResponse(
            id=gen.id,
            stl_url=f"/exports/{stl_filename}.stl",
            step_url=f"/exports/{stl_filename}.step",
            code=code,
            parameters=params,
            part_type=part_type,
            status="completed",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(Generation).count()
    items = db.query(Generation).order_by(Generation.created_at.desc()).offset(skip).limit(limit).all()

    return HistoryResponse(
        items=[
            HistoryItem(
                id=g.id,
                prompt=g.prompt,
                part_type=g.part_type,
                parameters=json.loads(g.parameters) if g.parameters else {},
                stl_url=f"/exports/{Path(g.stl_path).name}" if g.stl_path else "",
                created_at=g.created_at.isoformat() if g.created_at else "",
                status=g.status,
            )
            for g in items
        ],
        total=total,
    )


@router.get("/generation/{gen_id}")
async def get_generation(gen_id: int, db: Session = Depends(get_db)):
    gen = db.query(Generation).filter(Generation.id == gen_id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="未找到生成记录")

    return {
        "id": gen.id,
        "prompt": gen.prompt,
        "part_type": gen.part_type,
        "parameters": json.loads(gen.parameters) if gen.parameters else {},
        "stl_url": f"/exports/{Path(gen.stl_path).name}" if gen.stl_path else "",
        "step_url": f"/exports/{Path(gen.step_path).name}" if gen.step_path else "",
        "code": gen.cad_code,
        "status": gen.status,
        "created_at": gen.created_at.isoformat() if gen.created_at else "",
    }


# ============================================================
# STEP 1: 工程约束检查
# ============================================================

@router.post("/constraint/check")
async def constraint_check(request: dict):
    """工程约束检查 + 自动修复

    请求体: {"part_type": "motor_mount", "params": {...}}
    """
    from ..constraint_engine import check_and_fix

    part_type = request.get("part_type", "")
    params = request.get("params", {})

    if not part_type:
        raise HTTPException(status_code=400, detail="part_type 不能为空")

    result = check_and_fix(part_type, params)
    return result


# ============================================================
# STEP 2: 多方案生成
# ============================================================

@router.post("/design/generate")
async def design_generate(request: dict):
    """多方案设计空间生成

    请求体: {
        "part_type": "motor_mount",
        "base_params": {"base_length": 60, ...},
        "requirements": {"load": "light", "material": "PLA"}
    }
    """
    from ..design_generator import generate_design_space

    part_type = request.get("part_type", "")
    base_params = request.get("base_params", {})
    requirements = request.get("requirements", {})

    if not part_type:
        raise HTTPException(status_code=400, detail="part_type 不能为空")

    result = generate_design_space(part_type, base_params, requirements)
    return result


# ============================================================
# STEP 3: 自动装配
# ============================================================

@router.post("/assembly/build")
async def assembly_build(request: dict):
    """自动装配构建

    请求体: {
        "parts": [{"name": "motor", "part_type": "motor", "params": {...}}, ...],
        "constraints": [{"type": "fixed_to", "part_a": "motor", "part_b": "bracket"}, ...]
    }
    """
    from ..assembly_engine import build_assembly

    parts = request.get("parts", [])
    constraints = request.get("constraints", [])

    if not parts:
        raise HTTPException(status_code=400, detail="parts 不能为空")

    result = build_assembly(parts, constraints)
    return result


# ============================================================
# 统一入口：自然语言 → 多方案生成
# ============================================================

@router.post("/generate-variants")
async def generate_variants(request: dict):
    """自然语言 → 设计意图解析 → 多方案生成（核心产品接口）

    请求体: {"prompt": "做一个轻量化电机支架，适配M4螺丝"}
    """
    from ..llm import generate_from_prompt

    prompt = request.get("prompt", "")
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt 不能为空")

    result = generate_from_prompt(prompt)
    return result


# ============================================================
# 几何校验
# ============================================================

@router.post("/validate/geometry")
async def validate_geometry_endpoint(request: dict):
    """几何校验 API

    请求体: {"geometry_info": {...}}
    """
    from ..engineering.validation import validate_geometry
    from ..logger import log_validation

    geometry = request.get("geometry")
    result = validate_geometry(geometry)
    log_validation("geometry", result.valid, result.errors)
    return result.to_dict()


# ============================================================
# 制造校验
# ============================================================

@router.post("/validate/manufacturing")
async def validate_manufacturing_endpoint(request: dict):
    """制造校验 API

    请求体: {"params": {...}, "processes": ["fdm_3d_print"]}
    """
    from ..engineering.validation import validate_manufacturing
    from ..logger import log_validation

    params = request.get("params", {})
    processes = request.get("processes")
    result = validate_manufacturing(params, processes)
    log_validation("manufacturing", result["valid"], result.get("issues", []))
    return result


# ============================================================
# 碰撞检测
# ============================================================

@router.post("/validate/collision")
async def validate_collision_endpoint(request: dict):
    """装配碰撞检测 API

    请求体: {"parts": [{"name": "xxx", "aabb": {...}}, ...]}
    """
    from ..engineering.validation import check_assembly_collisions, AABB

    parts_data = request.get("parts", [])
    parts_with_aabbs = []
    for p in parts_data:
        aabb_data = p.get("aabb", {})
        aabb = AABB(
            min_x=aabb_data.get("min_x", 0), min_y=aabb_data.get("min_y", 0),
            min_z=aabb_data.get("min_z", 0), max_x=aabb_data.get("max_x", 0),
            max_y=aabb_data.get("max_y", 0), max_z=aabb_data.get("max_z", 0),
        )
        parts_with_aabbs.append((p.get("name", ""), aabb))

    return check_assembly_collisions(parts_with_aabbs)


# ============================================================
# 自动修复
# ============================================================

@router.post("/repair")
async def repair_endpoint(request: dict):
    """自动修复 API

    请求体: {"params": {...}, "issues": [...], "part_type": "bracket"}
    """
    from ..engineering.repair import auto_repair
    from ..logger import log_repair

    params = request.get("params", {})
    issues = request.get("issues", [])

    result = auto_repair(params, issues)
    log_repair(request.get("part_type", ""), params, result.repaired_params, result.applied_fixes)
    return result.to_dict()


@router.post("/repair/full")
async def full_repair_endpoint(request: dict):
    """完整修复流水线 API

    请求体: {"params": {...}, "part_type": "bracket"}
    """
    from ..engineering.repair import full_repair_pipeline
    from ..logger import log_repair

    params = request.get("params", {})
    part_type = request.get("part_type", "")
    geometry = request.get("geometry")

    result = full_repair_pipeline(params, geometry, part_type)
    log_repair(part_type, params, result.repaired_params, result.applied_fixes)
    return result.to_dict()


# ============================================================
# BOM 生成
# ============================================================

@router.post("/bom/generate")
async def bom_generate_endpoint(request: dict):
    """BOM 生成 API

    请求体: {"parts": [{"name": "xxx", "part_type": "bracket", "params": {...}}]}
    """
    from ..engineering.bom import generate_bom_from_parts

    parts = request.get("parts", [])
    title = request.get("title", "Bill of Materials")

    bom = generate_bom_from_parts(parts, title)
    return bom.to_dict()


@router.post("/bom/export/csv")
async def bom_export_csv_endpoint(request: dict):
    """BOM 导出 CSV API"""
    from ..engineering.bom import generate_bom_from_parts, bom_to_csv

    parts = request.get("parts", [])
    bom = generate_bom_from_parts(parts)
    return {"csv": bom_to_csv(bom)}


# ============================================================
# 依赖图
# ============================================================

@router.post("/dependency/check")
async def dependency_check_endpoint(request: dict):
    """依赖图检查 API

    请求体: {"nodes": [...], "edges": [...]}
    """
    from ..engineering.constraints import DependencyGraph

    graph = DependencyGraph()
    node_ids = {}

    for n in request.get("nodes", []):
        nid = graph.add_node(n.get("name", ""), n.get("type", "parameter"), n.get("data", {}))
        node_ids[n.get("name", "")] = nid

    for e in request.get("edges", []):
        src = node_ids.get(e.get("source", ""))
        tgt = node_ids.get(e.get("target", ""))
        if src and tgt:
            graph.add_edge(src, tgt)

    return {
        "has_cycle": graph.has_cycle(),
        "topological_order": graph.get_topological_order() if not graph.has_cycle() else [],
        "graph": graph.to_dict(),
    }
