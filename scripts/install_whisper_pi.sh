#!/usr/bin/env bash
set -e

# ============================================================================
# Whisper.cpp Installation Script for Raspberry Pi
# Speech-to-Text engine for Antonio
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🎤 Installing Whisper.cpp for Antonio Voice System    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

INSTALL_DIR="$HOME/antonio-voice"
WHISPER_DIR="$INSTALL_DIR/whisper.cpp"

# Create installation directory
echo "[1/6] Creating installation directory..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Install dependencies
echo "[2/6] Installing build dependencies..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils

# Clone whisper.cpp
echo "[3/6] Cloning whisper.cpp..."
if [ -d "$WHISPER_DIR" ]; then
    echo "  Directory exists, pulling latest..."
    cd "$WHISPER_DIR"
    git pull
else
    git clone https://github.com/ggerganov/whisper.cpp.git
    cd "$WHISPER_DIR"
fi

# Build whisper.cpp
echo "[4/6] Building whisper.cpp (this may take 5-10 minutes)..."
make clean
make

# Download Italian model (base - good balance speed/accuracy)
echo "[5/6] Downloading Whisper base model (bilingual IT/EN)..."
bash ./models/download-ggml-model.sh base

echo "[6/6] Testing whisper..."
if [ -f "./main" ]; then
    echo "✓ Whisper.cpp built successfully!"
    echo "✓ Model downloaded: models/ggml-base.bin"
else
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ Whisper.cpp Installation Complete!        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Installation directory: $WHISPER_DIR"
echo "Model: models/ggml-base.bin (74MB)"
echo ""
echo "Test with:"
echo "  cd $WHISPER_DIR"
echo "  ./main -m models/ggml-base.bin -f samples/jfk.wav"
echo ""
