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
