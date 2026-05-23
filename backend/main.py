"""FastAPI main application for the AI CAD Platform."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import router
from .database import init_db

BASE_DIR = Path(__file__).parent
EXPORTS_DIR = BASE_DIR / "exports"
RENDERS_DIR = BASE_DIR / "renders"

EXPORTS_DIR.mkdir(exist_ok=True)
RENDERS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="AI Mechanical CAD Studio",
    description="AI 参数化 CAD 生成平台",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "https://cad.myonlyheart.xyz",
        "https://frontend-12lwc0cwm-myheart-s-projects.vercel.app",
        "https://frontend-kappa-henna-67.vercel.app",
        "https://mechanical-ai-cad-myheart-s-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/exports", StaticFiles(directory=str(EXPORTS_DIR)), name="exports")
app.mount("/renders", StaticFiles(directory=str(RENDERS_DIR)), name="renders")
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    init_db()
    print("AI Mechanical CAD Studio 启动成功!")


@app.get("/")
async def root():
    return {"name": "AI Mechanical CAD Studio", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
