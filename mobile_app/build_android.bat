@echo off
chcp 65001 >nul
echo ========================================
echo   Time Tracker Android 构建脚本
echo ========================================
echo.

REM 检查 Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

REM 检查 npm
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 npm
    pause
    exit /b 1
)

echo [1/5] 安装依赖...
call npm install
if %errorlevel% neq 0 (
    echo [错误] npm install 失败
    pause
    exit /b 1
)

echo.
echo [2/5] 构建 Web 资源...
call npm run build
if %errorlevel% neq 0 (
    echo [错误] Vite 构建失败
    pause
    exit /b 1
)

echo.
echo [3/5] 检查 Android 平台...
if not exist "android" (
    echo 添加 Android 平台...
    call npx cap add android
    if %errorlevel% neq 0 (
        echo [错误] 添加 Android 平台失败
        pause
        exit /b 1
    )
)

echo.
echo [4/5] 同步到 Android 项目...
call npx cap sync android
if %errorlevel% neq 0 (
    echo [错误] Capacitor 同步失败
    pause
    exit /b 1
)

echo.
echo [5/5] 打开 Android Studio...
echo.
echo ========================================
echo   构建完成！
echo ========================================
echo.
echo 接下来请在 Android Studio 中:
echo 1. 等待 Gradle 同步完成
echo 2. 选择 Build ^> Build Bundle(s) / APK(s) ^> Build APK(s)
echo 3. APK 将生成在 android/app/build/outputs/apk/debug/
echo.
echo 或者使用命令行构建:
echo   cd android ^&^& gradlew assembleDebug
echo.

call npx cap open android

pause
