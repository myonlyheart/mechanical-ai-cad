@echo off
echo ========================================
echo  AI CAD 平台 - 安装
echo ========================================
echo.

cd /d "%~dp0\.."

echo [1/4] 创建Python虚拟环境...
python -m venv .venv
if errorlevel 1 (
    echo 错误: 创建虚拟环境失败
    pause
    exit /b 1
)

echo [2/4] 安装Python依赖...
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r backend\requirements.txt

echo [3/4] 安装Node.js依赖...
cd frontend
call npm install
cd ..

echo [4/4] 创建目录...
if not exist backend\exports mkdir backend\exports
if not exist backend\renders mkdir backend\renders
if not exist backend\database mkdir backend\database

echo.
echo 安装完成！
echo 运行 start.bat 启动应用
pause
