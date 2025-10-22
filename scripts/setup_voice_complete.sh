#!/usr/bin/env bash
set -e

# ============================================================================
# Antonio Voice System - Complete Setup Script for Raspberry Pi
# Installs: Whisper.cpp (STT) + Piper-TTS (TTS) + Voice Pipeline
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🎤 Antonio Complete Voice System Installation       ║"
echo "║                    Raspberry Pi Setup                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Install Whisper.cpp
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 1: Installing Whisper.cpp (STT)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash ~/antonio-evo/scripts/install_whisper_pi.sh

echo ""
read -p "✓ Whisper.cpp installed. Press ENTER to continue..."
echo ""

# Step 2: Install Piper-TTS
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 2: Installing Piper-TTS (TTS)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash ~/antonio-evo/scripts/install_piper_pi.sh

echo ""
read -p "✓ Piper-TTS installed. Press ENTER to continue..."
echo ""

# Step 3: Install Python dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 3: Installing Python dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ~/antonio-evo
source .venv/bin/activate

pip install --upgrade pip
pip install pyaudio requests

echo "✓ Python dependencies installed"
echo ""

# Step 4: Make voice script executable
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 4: Setting up voice pipeline"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

chmod +x ~/antonio-evo/antonio_voice.py

echo "✓ Voice pipeline ready"
echo ""

# Step 5: Test components
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 5: Testing components"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "[1/2] Testing Piper-TTS..."
~/antonio-voice/piper/speak.sh "Ciao, sono Antonio. Il sistema vocale è pronto!"
echo "✓ TTS working!"

echo ""
echo "[2/2] Testing Whisper.cpp..."
if [ -f ~/antonio-voice/whisper.cpp/samples/jfk.wav ]; then
    cd ~/antonio-voice/whisper.cpp
    ./main -m models/ggml-base.bin -f samples/jfk.wav > /dev/null 2>&1
    echo "✓ STT working!"
else
    echo "⚠️  No sample audio, skipping Whisper test"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║            ✅ INSTALLATION COMPLETE!                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🎤 Antonio Voice System is ready!"
echo ""
echo "Components installed:"
echo "  ✓ Whisper.cpp (STT) - ~/antonio-voice/whisper.cpp"
echo "  ✓ Piper-TTS (TTS)   - ~/antonio-voice/piper"
echo "  ✓ Voice Pipeline    - ~/antonio-evo/antonio_voice.py"
echo ""
echo "To start the voice system:"
echo "  1. Start Antonio server (in another terminal):"
echo "     cd ~/antonio-evo"
echo "     source .venv/bin/activate"
echo "     python3 api/server.py"
echo ""
echo "  2. Start voice system:"
echo "     cd ~/antonio-evo"
echo "     source .venv/bin/activate"
echo "     python3 antonio_voice.py"
echo ""
echo "🎉 Enjoy talking with Antonio!"
echo ""
