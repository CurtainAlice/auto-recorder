@echo off
chcp 65001 >nul
echo ========================================
echo   鼠标键盘录制回放工具 打包脚本
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 安装依赖
echo 📦 安装依赖包...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo 🔨 开始打包...
pyinstaller --onefile --windowed --name "鼠标键盘录制回放工具" --clean auto_recorder_gui.py

if errorlevel 1 (
    echo ❌ 打包失败
    pause
    exit /b 1
)

echo.
echo ✅ 打包完成！
echo 📁 可执行文件在：dist\鼠标键盘录制回放工具.exe
echo.
pause
