"""FastAPI main application for the AI CAD Platform."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response, FileResponse
from starlette.middleware.wsgi import WSGIMiddleware

from .api import router
from .database import init_db

BASE_DIR = Path(__file__).parent
EXPORTS_DIR = BASE_DIR / "exports"
RENDERS_DIR = BASE_DIR / "renders"
STATIC_DIR = BASE_DIR.parent / "static_export"

EXPORTS_DIR.mkdir(exist_ok=True)
RENDERS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="AI Mechanical CAD Studio",
    description="AI 参数化 CAD 生成平台",
    version="1.1.0",
)

# CORS — 只允许本地开发 + 生产域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "https://cad.myonlyheart.xyz",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(router, prefix="/api/v1")

# 健康检查（在 API 路由内，不被静态文件拦截）
@app.get("/api/health")
async def health():
    return {"status": "ok"}

# 静态文件 (STL/STEP 导出)
app.mount("/exports", StaticFiles(directory=str(EXPORTS_DIR)), name="exports")
app.mount("/renders", StaticFiles(directory=str(RENDERS_DIR)), name="renders")

# 前端静态页面 — 必须放在最后作为 catch-all
if STATIC_DIR.exists() and any(STATIC_DIR.iterdir()):
    _index_html = STATIC_DIR / "index.html"

    @app.get("/")
    @app.get("/{path:path}")
    async def serve_frontend(path: str = ""):
        # 只服务已知 API/静态路径之外的请求
        # API 路由已优先匹配，不会到达这里
        file_path = STATIC_DIR / path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_index_html))


@app.on_event("startup")
async def startup_event():
    init_db()
    has_frontend = STATIC_DIR.exists() and any(STATIC_DIR.iterdir())
    print(f"AI Mechanical CAD Studio v1.1.0 启动成功!")
    print(f"  前端: {'已托管' if has_frontend else '未构建 (运行 npm run build)'}")
    print(f"  API:  http://localhost:8000/api/v1")
    print(f"  文档: http://localhost:8000/docs")
