@echo off
echo ========================================
echo  AI 参数化 CAD 生成器
echo ========================================
echo.

cd /d "%~dp0"

:: 检查虚拟环境
if not exist .venv\Scripts\activate.bat (
    echo 虚拟环境不存在，请先运行 scripts\install.bat
    pause
    exit /b 1
)

:: 检查node_modules
if not exist frontend\node_modules (
    echo 依赖未安装，请先运行 scripts\install.bat
    pause
    exit /b 1
)

echo 启动后端服务器...
start "CAD 后端" cmd /k "call .venv\Scripts\activate.bat && cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo 等待后端初始化...
timeout /t 3 /nobreak > nul

echo 启动前端服务器...
start "CAD 前端" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo  服务器启动中...
echo  后端: http://localhost:8000
echo  前端: http://localhost:3000
echo  API文档: http://localhost:8000/docs
echo ========================================
echo.
pause
