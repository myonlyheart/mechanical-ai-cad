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
    BearingBlock, BearingBlockParams,
    Flange, FlangeParams,
    Coupling, CouplingParams,
    ShaftSleeve, ShaftSleeveParams,
    export_stl, export_step,
)
from ..components.fasteners import Bolt, BoltParams, Nut, NutParams, Washer, WasherParams
from ..components.shafts import Shaft, ShaftParams
from ..components.bearings import Bearing, BearingParams
from ..components.gears import Gear, GearParams

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
    elif part_type == "bearing_block":
        return f'''from build123d import *
from cad import BearingBlock, BearingBlockParams

params = BearingBlockParams(
    base_length={params.get("base_length", 60)},
    base_width={params.get("base_width", 40)},
    bearing_diameter={params.get("bearing_diameter", 22)},
    height={params.get("height", 30)},
)
block = BearingBlock(params)
part = block.build()
'''
    elif part_type == "flange":
        return f'''from build123d import *
from cad import Flange, FlangeParams

params = FlangeParams(
    outer_diameter={params.get("outer_diameter", 80)},
    bore_diameter={params.get("bore_diameter", 30)},
    bolt_count={params.get("bolt_count", 6)},
    thickness={params.get("thickness", 8)},
)
flange = Flange(params)
part = flange.build()
'''
    elif part_type == "coupling":
        return f'''from build123d import *
from cad import Coupling, CouplingParams

params = CouplingParams(
    outer_diameter={params.get("outer_diameter", 30)},
    length={params.get("length", 40)},
    bore_diameter={params.get("bore_diameter", 8)},
)
coupling = Coupling(params)
part = coupling.build()
'''
    elif part_type == "shaft_sleeve":
        return f'''from build123d import *
from cad import ShaftSleeve, ShaftSleeveParams

params = ShaftSleeveParams(
    outer_diameter={params.get("outer_diameter", 20)},
    inner_diameter={params.get("inner_diameter", 12)},
    length={params.get("length", 30)},
)
sleeve = ShaftSleeve(params)
part = sleeve.build()
'''
    elif part_type == "bolt":
        return f'''from build123d import *
from components.fasteners import Bolt, BoltParams

params = BoltParams(
    diameter={params.get("diameter", 6)},
    length={params.get("length", 20)},
    head_type="{params.get("head_type", "hex")}",
)
bolt = Bolt(params)
part = bolt.build()
'''
    elif part_type == "nut":
        return f'''from build123d import *
from components.fasteners import Nut, NutParams

params = NutParams(
    diameter={params.get("diameter", 6)},
    nut_type="{params.get("nut_type", "hex")}",
)
nut = Nut(params)
part = nut.build()
'''
    elif part_type == "washer":
        return f'''from build123d import *
from components.fasteners import Washer, WasherParams

params = WasherParams(
    inner_diameter={params.get("inner_diameter", 6.5)},
    outer_diameter={params.get("outer_diameter", 12)},
    washer_type="{params.get("washer_type", "flat")}",
)
washer = Washer(params)
part = washer.build()
'''
    elif part_type == "shaft":
        return f'''from build123d import *
from components.shafts import Shaft, ShaftParams

params = ShaftParams(
    diameter={params.get("diameter", 8)},
    length={params.get("length", 120)},
    shaft_type="{params.get("shaft_type", "round")}",
    keyway_width={params.get("keyway_width", 0)},
)
shaft = Shaft(params)
part = shaft.build()
'''
    elif part_type == "bearing":
        return f'''from build123d import *
from components.bearings import Bearing, BearingParams

params = BearingParams(
    inner_diameter={params.get("inner_diameter", 8)},
    outer_diameter={params.get("outer_diameter", 22)},
    width={params.get("width", 7)},
    bearing_type="{params.get("bearing_type", "deep_groove")}",
)
bearing = Bearing(params)
part = bearing.build()
'''
    elif part_type == "gear":
        return f'''from build123d import *
from components.gears import Gear, GearParams

params = GearParams(
    module={params.get("module", 2)},
    tooth_count={params.get("tooth_count", 20)},
    face_width={params.get("face_width", 10)},
    gear_type="{params.get("gear_type", "spur")}",
    helix_angle={params.get("helix_angle", 0)},
    bore_diameter={params.get("bore_diameter", 8)},
)
gear = Gear(params)
part = gear.build()
'''
    return "# 不支持的零件类型"


def build_part(part_type: str, params: dict):
    if part_type == "bracket":
        p = LBracketParams(**{k: v for k, v in params.items() if hasattr(LBracketParams, k)})
        return LBracket(p).build()
    elif part_type == "gear":
        p = GearParams(**{k: v for k, v in params.items() if hasattr(GearParams, k)})
        return Gear(p).build()
    elif part_type == "motor_mount":
        p = NEMA17MountParams(**{k: v for k, v in params.items() if hasattr(NEMA17MountParams, k)})
        return NEMA17Mount(p).build()
    elif part_type == "bearing_block":
        p = BearingBlockParams(**{k: v for k, v in params.items() if hasattr(BearingBlockParams, k)})
        return BearingBlock(p).build()
    elif part_type == "flange":
        p = FlangeParams(**{k: v for k, v in params.items() if hasattr(FlangeParams, k)})
        return Flange(p).build()
    elif part_type == "coupling":
        p = CouplingParams(**{k: v for k, v in params.items() if hasattr(CouplingParams, k)})
        return Coupling(p).build()
    elif part_type == "shaft_sleeve":
        p = ShaftSleeveParams(**{k: v for k, v in params.items() if hasattr(ShaftSleeveParams, k)})
        return ShaftSleeve(p).build()
    elif part_type == "bolt":
        p = BoltParams(**{k: v for k, v in params.items() if hasattr(BoltParams, k)})
        return Bolt(p).build()
    elif part_type == "nut":
        p = NutParams(**{k: v for k, v in params.items() if hasattr(NutParams, k)})
        return Nut(p).build()
    elif part_type == "washer":
        p = WasherParams(**{k: v for k, v in params.items() if hasattr(WasherParams, k)})
        return Washer(p).build()
    elif part_type == "shaft":
        p = ShaftParams(**{k: v for k, v in params.items() if hasattr(ShaftParams, k)})
        return Shaft(p).build()
    elif part_type == "bearing":
        p = BearingParams(**{k: v for k, v in params.items() if hasattr(BearingParams, k)})
        return Bearing(p).build()
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


# ============================================================
# 紧固件系统
# ============================================================

@router.post("/fasteners/hole-match")
async def hole_match_endpoint(request: dict):
    """螺丝孔匹配 API

    请求体: {"bolt_diameter": 6, "hole_type": "normal"}
    """
    from ..components.fasteners import get_hole_diameter, get_counterbore_dimensions, get_countersink_diameter

    bolt_d = request.get("bolt_diameter", 6)
    hole_type = request.get("hole_type", "normal")

    return {
        "bolt_diameter": bolt_d,
        "hole_type": hole_type,
        "hole_diameter": get_hole_diameter(bolt_d, hole_type),
        "counterbore": get_counterbore_dimensions(bolt_d),
        "countersink_diameter": get_countersink_diameter(bolt_d),
    }


@router.post("/fasteners/auto-assembly")
async def fastener_auto_assembly_endpoint(request: dict):
    """自动紧固件装配 API

    请求体: {
        "anchors": [{"name": "h1", "type": "hole_center", "diameter": 6.5, "position": [x,y,z]}],
        "plate_thickness": 10,
        "bolt_diameter": 0 (auto)
    }
    """
    from ..components.fasteners import auto_fasten

    anchors = request.get("anchors", [])
    plate_thickness = request.get("plate_thickness", 10.0)
    bolt_d = request.get("bolt_diameter", 0)

    result = auto_fasten(anchors, plate_thickness, preferred_diameter=bolt_d)
    return result.to_dict()


# ============================================================
# 轴系统
# ============================================================

@router.post("/shafts/fit")
async def shaft_fit_endpoint(request: dict):
    """轴配合查询 API

    请求体: {"shaft_diameter": 8, "fit_type": "H7/k6", "purpose": "shaft|bearing|gear", "bearing_series": "6205", "gear_module": 2}
    """
    from ..components.shafts import get_shaft_fit, get_bearing_fit, get_gear_fit

    shaft_d = request.get("shaft_diameter", 8)
    purpose = request.get("purpose", "shaft")

    if purpose == "bearing":
        return get_bearing_fit(shaft_d, request.get("bearing_series", ""))
    elif purpose == "gear":
        return get_gear_fit(shaft_d, request.get("gear_module", 0))
    else:
        return get_shaft_fit(shaft_d, request.get("fit_type", "H7/k6"))


# ============================================================
# 齿轮传动系统
# ============================================================

@router.post("/gears/drive")
async def gear_drive_endpoint(request: dict):
    """自动传动系统设计 API

    请求体: {"target_ratio": 3.0, "module": 2.0, "max_stages": 2}
    """
    from ..components.gears import auto_select_gears

    target_ratio = request.get("target_ratio", 1.0)
    module = request.get("module", 2.0)
    min_teeth = request.get("min_teeth", 12)
    max_teeth = request.get("max_teeth", 80)
    max_stages = request.get("max_stages", 2)

    result = auto_select_gears(target_ratio, module, min_teeth, max_teeth, max_stages)
    return result.to_dict()


# ============================================================
# 工程语义校验
# ============================================================

@router.post("/validate/engineering")
async def validate_engineering_endpoint(request: dict):
    """工程语义校验 API

    请求体: {"parts": [{"name": "g1", "part_type": "gear", "params": {"module": 2, ...}}, ...]}
    """
    from ..engineering.validation import validate_assembly

    parts = request.get("parts", [])
    result = validate_assembly(parts)
    return result.to_dict()


# ============================================================
# 电机系统
# ============================================================

@router.get("/motors/list")
async def motors_list_endpoint(motor_type: str = ""):
    """电机列表 API

    Query参数: motor_type=stepper|dc|servo (可选)
    """
    from ..components.motors import list_motors
    return {"motors": list_motors(motor_type)}


@router.post("/motors/mount")
async def motors_mount_endpoint(request: dict):
    """电机安装座参数 API

    请求体: {"motor_name": "NEMA17"}
    """
    from ..components.motors import get_mount_params

    motor_name = request.get("motor_name", "")
    return get_mount_params(motor_name)


@router.post("/motors/coupling")
async def motors_coupling_endpoint(request: dict):
    """联轴器推荐 API

    请求体: {"shaft_diameter": 8, "motor_name": "NEMA17"}
    """
    from ..components.motors import recommend_coupling

    shaft_d = request.get("shaft_diameter", 8)
    motor_name = request.get("motor_name", "")
    return recommend_coupling(shaft_d, motor_name)


# ============================================================
# 线性运动系统
# ============================================================

@router.get("/rails/list")
async def rails_list_endpoint():
    """导轨列表 API"""
    from ..components.rails import list_rails, list_screws
    return {"rails": list_rails(), "screws": list_screws()}


@router.post("/rails/calculate")
async def rails_calculate_endpoint(request: dict):
    """运动计算 API

    请求体: {"rail_name": "MGN12", "rail_length": 300, "screw_name": "T8x8", "microstepping": 16}
    """
    from ..components.rails import get_rail_spec, get_screw_spec, calculate_travel, calculate_steps_per_mm

    result = {}

    rail_name = request.get("rail_name", "")
    if rail_name:
        spec = get_rail_spec(rail_name)
        if spec:
            rail_length = request.get("rail_length", 300)
            result["rail"] = spec.to_dict()
            result["travel"] = calculate_travel(rail_length, spec.block_length)

    screw_name = request.get("screw_name", "")
    if screw_name:
        spec = get_screw_spec(screw_name)
        if spec:
            microstepping = request.get("microstepping", 16)
            result["screw"] = spec.to_dict()
            result["steps_per_mm"] = calculate_steps_per_mm(screw_name, 1.8, microstepping)

    return result
