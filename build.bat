@echo off
setlocal
cd /d "%~dp0"

if not exist icon.ico (
    echo Generating icon...
    python make_icon.py || goto :err
)

echo Building TimeTimer.exe...
python -m PyInstaller --onefile --windowed --name TimeTimer ^
    --icon "%cd%\icon.ico" ^
    --distpath . --workpath build --specpath build --noconfirm ^
    timer.py || goto :err

rmdir /s /q build 2>nul
rmdir /s /q __pycache__ 2>nul
echo Done. TimeTimer.exe ready.
exit /b 0

:err
echo Build failed.
exit /b 1
