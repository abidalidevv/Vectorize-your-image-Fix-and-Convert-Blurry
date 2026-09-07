@echo off
setlocal enabledelayedexpansion
title VectorForge AI ? Downloading AI Models

echo =====================================================================
echo           VectorForge AI -- AI Models Downloader
echo =====================================================================
echo.
echo This script will check and download all required AI models:
echo   1. YuNet Face Detector (OpenCV Zoo)
echo   2. GFPGAN v1.4 (Face Restoration)
echo   3. LaMa FP32 (Magic Eraser Inpainting)
echo   4. Real-ESRGAN v3 Fast + RealESRGAN_x4plus Ultra (Upscaler)
echo   5. BiRefNet Ultra + ISNet (Background Remover)
echo.
echo =====================================================================

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in your PATH!
    echo Please install Python 3.10+ and make sure to check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

if exist "backend\venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment in backend\venv...
    call "backend\venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment in venv...
    call "venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment in .venv...
    call ".venv\Scripts\activate.bat"
)

echo.
echo [1/2] Checking and Downloading Face Restorer and Magic Eraser Models...
echo ---------------------------------------------------------------------
python scripts/download_new_models.py
if errorlevel 1 (
    echo [WARNING] Some models in step 1 encountered issues.
)

echo.
echo [2/2] Checking and Downloading Pro Models (Upscalers and BG Remover)...
echo ---------------------------------------------------------------------
python scripts/download_pro_models.py
if errorlevel 1 (
    echo [WARNING] Some models in step 2 encountered issues.
)

echo.
echo =====================================================================
echo   All downloads checked! VectorForge AI is ready for offline use.
echo =====================================================================
echo.
pause
