#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "====================================================================="
echo "          VectorForge AI -- AI Models Downloader"
echo "====================================================================="
echo ""

if [ -f "backend/venv/bin/activate" ]; then
    echo "[INFO] Activating virtual environment in backend/venv..."
    source "backend/venv/bin/activate"
elif [ -f "venv/bin/activate" ]; then
    echo "[INFO] Activating virtual environment in venv..."
    source "venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Activating virtual environment in .venv..."
    source ".venv/bin/activate"
fi

echo "[1/2] Checking and Downloading Face Restorer and Magic Eraser Models..."
echo "---------------------------------------------------------------------"
python scripts/download_new_models.py

echo ""
echo "[2/2] Checking and Downloading Pro Models (Upscalers and BG Remover)..."
echo "---------------------------------------------------------------------"
python scripts/download_pro_models.py

echo ""
echo "====================================================================="
echo "  All downloads checked! VectorForge AI is ready for offline use."
echo "====================================================================="
