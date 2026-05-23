# AI Mechanical CAD Studio

AI 参数化 CAD 生成平台 - 从自然语言描述自动生成机械零件

## 快速启动

```bash
# Windows 双击运行
start.bat

# 或手动启动
# 终端1: 后端
cd backend
uvicorn main:app --reload

# 终端2: 前端
cd frontend
npm run dev
```

访问: http://localhost:3000

## 功能

- 自然语言生成 CAD 模型
- 3D 在线预览
- STL/STEP 导出
- 参数化编辑

## 技术栈

- Frontend: Next.js + Three.js
- Backend: FastAPI + build123d
- Database: SQLite
