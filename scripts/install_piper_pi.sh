#!/usr/bin/env bash
set -e

# ============================================================================
# Piper-TTS Installation Script for Raspberry Pi
# Natural Text-to-Speech for Antonio
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      🔊 Installing Piper-TTS for Antonio Voice System     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

INSTALL_DIR="$HOME/antonio-voice"
PIPER_DIR="$INSTALL_DIR/piper"

# Create installation directory
echo "[1/5] Creating installation directory..."
mkdir -p "$PIPER_DIR"
cd "$PIPER_DIR"

# Download Piper for ARM64 (Raspberry Pi)
echo "[2/5] Downloading Piper for ARM64..."
PIPER_VERSION="2024.3.13"
PIPER_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_aarch64.tar.gz"

wget -O piper.tar.gz "$PIPER_URL"
tar -xzf piper.tar.gz
rm piper.tar.gz

# Make executable
chmod +x piper/piper

# Download Italian voice model (riccardo - quality medium, fast)
echo "[3/5] Downloading Italian voice model (riccardo)..."
mkdir -p models
cd models

# Italian voice - Riccardo (medium quality, good speed)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/riccardo/medium/it_IT-riccardo-x_low.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/riccardo/medium/it_IT-riccardo-x_low.onnx.json

echo "[4/5] Testing Piper-TTS..."
cd "$PIPER_DIR"
echo "Ciao, sono Antonio!" | ./piper/piper \
    --model models/it_IT-riccardo-x_low.onnx \
    --output_file test_output.wav

if [ -f "test_output.wav" ]; then
    echo "✓ Piper-TTS working!"
    rm test_output.wav
else
    echo "❌ Piper test failed!"
    exit 1
fi

echo "[5/5] Creating convenience script..."
cat > "$PIPER_DIR/speak.sh" << 'EOF'
#!/bin/bash
# Quick TTS script
TEXT="$1"
if [ -z "$TEXT" ]; then
    echo "Usage: ./speak.sh 'Text to speak'"
    exit 1
fi

echo "$TEXT" | ~/antonio-voice/piper/piper/piper \
    --model ~/antonio-voice/piper/models/it_IT-riccardo-x_low.onnx \
    --output_file /tmp/speech.wav

aplay /tmp/speech.wav 2>/dev/null
rm /tmp/speech.wav
EOF

chmod +x "$PIPER_DIR/speak.sh"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ Piper-TTS Installation Complete!          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Installation directory: $PIPER_DIR"
echo "Voice model: it_IT-riccardo-x_low (Italian male)"
echo ""
echo "Test with:"
echo "  $PIPER_DIR/speak.sh 'Ciao, sono Antonio!'"
echo ""
