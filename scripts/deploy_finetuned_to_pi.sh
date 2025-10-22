#!/bin/bash
# Deploy Fine-Tuned Antonio to Raspberry Pi
# Run AFTER testing on Mac

set -e

echo "🍓 Deploying Fine-Tuned Antonio to Raspberry Pi"
echo "================================================"

# Check if model exists locally
if ! ollama list | grep -q "antonio-tools-finetuned"; then
    echo "❌ Model not found locally!"
    echo "   Run test_finetuned_mac.sh first!"
    exit 1
fi

PI_HOST="raspberrypi.local"
PI_USER="pi"

echo "📡 Target: $PI_USER@$PI_HOST"
echo ""

# Step 1: Transfer GGUF file
echo "📦 Step 1: Transferring GGUF to Pi..."

if [ ! -d ~/Downloads/antonio_gguf ]; then
    echo "❌ antonio_gguf directory not found in ~/Downloads"
    exit 1
fi

export SSHPASS="207575"
sshpass -e scp -r ~/Downloads/antonio_gguf "$PI_USER@$PI_HOST:/home/pi/"

echo "✅ Files transferred"

# Step 2: Create model on Pi
echo ""
echo "🔧 Step 2: Creating Ollama model on Pi..."

sshpass -e ssh "$PI_USER@$PI_HOST" << 'ENDSSH'
cd ~/antonio_gguf

# Find GGUF file
GGUF_FILE=$(find . -name "*.gguf" | head -1)

if [ -z "$GGUF_FILE" ]; then
    echo "❌ No GGUF file found!"
    exit 1
fi

echo "Found: $GGUF_FILE"

# Create Modelfile
cat > Modelfile.antonio-tools <<EOF
FROM ./$GGUF_FILE
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 8192

SYSTEM """You are Antonio, an intelligent assistant that knows when to use tools.

When you see large calculations, mention using CalculatorTool.
When you see factual questions, mention using WebSearchTool.
When questions are ambiguous, ask for clarification.
When calculations are simple (like 2+2), answer directly without tools.
"""
EOF

# Create model
ollama create antonio-tools-finetuned -f Modelfile.antonio-tools

echo "✅ Model created on Pi"
ENDSSH

# Step 3: Update Antonio server to use fine-tuned model
echo ""
echo "🔄 Step 3: Updating Antonio server..."

sshpass -e ssh "$PI_USER@$PI_HOST" << 'ENDSSH'
cd ~/antonio-evo/api

# Backup current server.py
cp server.py server.py.backup

# Update model name in server.py
sed -i 's/model_name = "gemma3:1b"/model_name = "antonio-tools-finetuned"/' server.py

echo "✅ Server updated to use fine-tuned model"
ENDSSH

# Step 4: Restart server
echo ""
echo "🔄 Step 4: Restarting Antonio server..."

sshpass -e ssh "$PI_USER@$PI_HOST" << 'ENDSSH'
# Stop current server
pkill -f "python3.*server.py" || true
sleep 2

# Start new server in background
cd ~/antonio-evo/api
nohup python3 server.py > /tmp/antonio.log 2>&1 &

sleep 3

# Check if running
if pgrep -f "python3.*server.py" > /dev/null; then
    echo "✅ Server started successfully"
else
    echo "❌ Server failed to start. Check /tmp/antonio.log"
fi
ENDSSH

# Step 5: Test on Pi
echo ""
echo "=========================================="
echo "🧪 TESTING ON RASPBERRY PI"
echo "=========================================="
echo ""

sleep 2

# Test API endpoint
echo "Test 1: Large calculation"
time curl -s -X POST http://$PI_HOST:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Calcola 1847 × 2935"}' \
  --max-time 45 | jq -r '.response' | head -5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Test 2: Simple calculation"
time curl -s -X POST http://$PI_HOST:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Quanto fa 2 + 2?"}' \
  --max-time 45 | jq -r '.response' | head -5

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "📊 What was deployed:"
echo "  ✅ Fine-tuned GGUF model"
echo "  ✅ Ollama model: antonio-tools-finetuned"
echo "  ✅ Updated server.py to use new model"
echo "  ✅ Server restarted"
echo ""
echo "🔗 Access:"
echo "  API: http://$PI_HOST:8000"
echo "  Chat: python3 /tmp/chat_antonio.py"
echo ""
echo "📝 Server log: /tmp/antonio.log on Pi"
echo ""
