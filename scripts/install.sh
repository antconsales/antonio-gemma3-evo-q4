#!/usr/bin/env bash
set -euo pipefail

echo "================================================"
echo "  Antonio Gemma3 Evo Q4 - Installation Script"
echo "================================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "✓ Detected: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    echo "✓ Detected: macOS"
else
    echo "⚠️  Unsupported OS: $OSTYPE"
    exit 1
fi

# Detect architecture
ARCH=$(uname -m)
echo "✓ Architecture: $ARCH"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Python: $PYTHON_VERSION"

# Check if we're on Raspberry Pi
IS_PI=0
if [[ -f /proc/device-tree/model ]] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    IS_PI=1
    PI_MODEL=$(cat /proc/device-tree/model)
    echo "✓ Running on: $PI_MODEL"
fi

echo ""
echo "Step 1: Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Step 2: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install GPIO libraries se su Pi
if [[ $IS_PI -eq 1 ]]; then
    echo "Step 3: Installing Raspberry Pi GPIO libraries..."
    pip install RPi.GPIO==0.7.1 || echo "⚠️  RPi.GPIO install failed (may need sudo)"
fi

echo ""
echo "Step 4: Setting up directories..."
mkdir -p data/evomemory/skills
mkdir -p data/models
mkdir -p logs

echo "Step 5: Initializing database..."
python3 -c "
from core.evomemory import EvoMemoryDB
db = EvoMemoryDB('data/evomemory/neurons.db')
print('✓ Database initialized')
db.close()
"

echo ""
echo "Step 6: Checking for model files..."

# Cerca modelli
MODELS_FOUND=0
MODEL_PATH=""

# Cerca in parent directory (artifacts/)
if [[ -f "../artifacts/gemma3-1b-q4_0.gguf" ]]; then
    echo "✓ Found model: ../artifacts/gemma3-1b-q4_0.gguf"
    ln -sf "$(realpath ../artifacts/gemma3-1b-q4_0.gguf)" data/models/
    MODELS_FOUND=1
    MODEL_PATH="../artifacts/gemma3-1b-q4_0.gguf"
fi

if [[ -f "../artifacts/gemma3-1b-q4_k_m.gguf" ]]; then
    echo "✓ Found model: ../artifacts/gemma3-1b-q4_k_m.gguf"
    ln -sf "$(realpath ../artifacts/gemma3-1b-q4_k_m.gguf)" data/models/
    MODELS_FOUND=1
fi

if [[ $MODELS_FOUND -eq 0 ]]; then
    echo "⚠️  No models found. Please download or quantize a model first."
    echo "   Run: bash ../scripts/quantize_gemma.sh"
fi

echo ""
echo "Step 7: Checking llama-cli..."
if [[ -f "../build/bin/llama-cli" ]]; then
    echo "✓ llama-cli found at ../build/bin/llama-cli"
else
    echo "⚠️  llama-cli not found. Please build llama.cpp first:"
    echo "   cd .. && cmake -B build && cmake --build build"
fi

echo ""
echo "================================================"
echo "  Installation complete! 🚀"
echo "================================================"
echo ""

if [[ $MODELS_FOUND -eq 1 ]]; then
    echo "Quick test:"
    echo "  source .venv/bin/activate"
    echo "  python3 api/server.py"
    echo ""
    echo "Then visit: http://localhost:8000/docs"
else
    echo "Before starting, download a model:"
    echo "  cd .. && bash scripts/quantize_gemma.sh"
fi

echo ""
echo "Need help? Check README.md"
echo ""

# Create systemd service se su Pi
if [[ $IS_PI -eq 1 ]]; then
    echo "💡 Tip: Install as systemd service?"
    echo "   sudo bash scripts/install_service.sh"
fi
