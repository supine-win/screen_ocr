@echo off
echo ========================================
echo MonitorOCR Windows 调试启动脚本
echo ========================================
echo.

REM 检查exe文件是否存在
if not exist "MonitorOCR_EasyOCR.exe" (
    echo 错误: MonitorOCR_EasyOCR.exe 不存在
    echo 请确保exe文件在当前目录中
    pause
    exit /b 1
)

REM 创建日志目录
if not exist "logs" mkdir logs

echo 1. 运行调试检查
echo 2. 启动应用 (无GUI模式)
echo 3. 启动应用 (GUI模式)
echo 4. 运行调试模式
echo 5. 查看日志
echo 6. 退出
echo.
set /p choice="请选择 (1-6): "
if "%choice%"=="1" (
    echo 正在运行调试检查...
    MonitorOCR_EasyOCR.exe -c "import debug_windows; debug_windows.main()"
) else if "%choice%"=="2" (
    echo 启动API服务器模式...
    echo 服务器将在 http://localhost:9501 运行
    echo 按 Ctrl+C 停止服务器
) else if "%choice%"=="3" (
    echo 启动GUI模式...
    MonitorOCR_EasyOCR.exe
) else if "%choice%"=="4" (
    echo 运行调试模式...
    MonitorOCR_EasyOCR.exe --debug
{{ ... }}
    echo 查看最新日志文件...
    if exist "logs\" (
        for /f %%i in ('dir logs\*.log /b /o:d') do set latest=%%i
        if defined latest (
            echo 最新日志文件: logs\!latest!
            type "logs\!latest!" | more
        ) else (
            echo 没有找到日志文件
        )
    ) else (
        echo 日志目录不存在
    )
) else if "%choice%"=="6" (
    echo 退出
    exit /b 0
) else (
    echo 无效选择
)

echo.
pause
