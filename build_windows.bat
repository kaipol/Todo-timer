@echo off
chcp 65001 >nul
echo ========================================
echo   Time Tracker Windows 构建脚本
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.12+
    pause
    exit /b 1
)

REM 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装 PyInstaller...
    pip install pyinstaller
)

REM 安装依赖
echo [步骤 1/3] 安装项目依赖...
pip install -r requirements.txt

REM 清理旧的构建文件
echo [步骤 2/3] 清理旧的构建文件...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM 执行构建
echo [步骤 3/3] 构建 Windows 可执行文件...
pyinstaller TimeTracker.spec

if errorlevel 1 (
    echo.
    echo [错误] 构建失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo   构建完成！
echo   输出文件: dist\TimeTracker.exe
echo ========================================
echo.

REM 询问是否运行
set /p run="是否立即运行? (y/n): "
if /i "%run%"=="y" (
    start "" "dist\TimeTracker.exe"
)

pause
