@echo off
REM 打包成目录版（onedir）：dist\BiliAudio\BiliAudio.exe
REM onedir 不解压到系统 Temp，对杀毒软件更友好；启动也更快。
REM 前提：.venv 已装好依赖（flask / yt-dlp）

cd /d "%~dp0"

echo 正在打包...
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean ^
  --onedir --console --name "BiliAudio" ^
  --icon "assets\icon.ico" ^
  --add-data "templates;templates" ^
  --add-data "assets;assets" ^
  --copy-metadata werkzeug --copy-metadata flask --copy-metadata yt-dlp ^
  --hidden-import=yt_dlp ^
  run.py

echo.
echo ========================================
echo 完成！运行: dist\BiliAudio\BiliAudio.exe
echo 可以把整个 BiliAudio 文件夹拷到任意位置使用
echo 使用前请确认已安装 FFmpeg: winget install FFmpeg
echo ========================================
pause
