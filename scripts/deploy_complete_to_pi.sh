#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Antonio Gemma3 Evo Q4 - Deploy to Pi
# Complete deployment script
# ========================================

# Configuration
RPI_HOST="${RPI_HOST:-192.168.1.24}"
RPI_USER="${RPI_USER:-o}"
RPI_PASS="${RPI_PASS:-207575}"
RPI_DIR="/home/${RPI_USER}/antonio-evo"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Antonio Gemma3 Evo Q4 - Deploy to Raspberry Pi              ║"
echo "╔═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Target: ${RPI_USER}@${RPI_HOST}"
echo "Remote dir: ${RPI_DIR}"
echo ""

# Function: SSH with password
ssh_cmd() {
    sshpass -p "${RPI_PASS}" ssh -o StrictHostKeyChecking=no "${RPI_USER}@${RPI_HOST}" "$@"
}

# Function: SCP with password
scp_cmd() {
    sshpass -p "${RPI_PASS}" scp -r -o StrictHostKeyChecking=no "$@" "${RPI_USER}@${RPI_HOST}:${RPI_DIR}/"
}

# Check sshpass
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}❌ sshpass not found!${NC}"
    echo "Install it:"
    echo "  macOS: brew install hudochenkov/sshpass/sshpass"
    echo "  Linux: sudo apt install sshpass"
    exit 1
fi

# Step 1: Test connection
echo -e "${YELLOW}[1/8]${NC} Testing connection to Pi..."
if ssh_cmd "echo 'Connection OK'"; then
    echo -e "${GREEN}✓ Connected to ${RPI_HOST}${NC}"
else
    echo -e "${RED}❌ Cannot connect to ${RPI_HOST}${NC}"
    exit 1
fi

# Step 2: Create remote directory
echo -e "${YELLOW}[2/8]${NC} Creating remote directory..."
ssh_cmd "mkdir -p ${RPI_DIR}/{data/evomemory/skills,data/models,logs}"
echo -e "${GREEN}✓ Directory created${NC}"

# Step 3: Deploy code
echo -e "${YELLOW}[3/8]${NC} Deploying antonio-evo code..."

# Create tarball (exclude venv, cache, db)
cd "$(dirname "$0")/.."
tar -czf /tmp/antonio-evo.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='*.db' \
    --exclude='data/evomemory/*.db' \
    --exclude='node_modules' \
    .

# Upload
sshpass -p "${RPI_PASS}" scp -o StrictHostKeyChecking=no \
    /tmp/antonio-evo.tar.gz "${RPI_USER}@${RPI_HOST}:/tmp/"

# Extract
ssh_cmd "cd ${RPI_DIR} && tar -xzf /tmp/antonio-evo.tar.gz && rm /tmp/antonio-evo.tar.gz"
echo -e "${GREEN}✓ Code deployed${NC}"

# Step 4: Deploy models
echo -e "${YELLOW}[4/8]${NC} Deploying models..."

MODEL_DIR="../artifacts"
if [ -f "${MODEL_DIR}/gemma3-1b-q4_0.gguf" ]; then
    echo "  Uploading Q4_0 model (720MB)..."
    sshpass -p "${RPI_PASS}" scp -o StrictHostKeyChecking=no \
        "${MODEL_DIR}/gemma3-1b-q4_0.gguf" \
        "${RPI_USER}@${RPI_HOST}:${RPI_DIR}/data/models/"
    echo -e "${GREEN}✓ Q4_0 uploaded${NC}"
else
    echo -e "${YELLOW}⚠️  Q4_0 model not found, skipping${NC}"
fi

if [ -f "${MODEL_DIR}/gemma3-1b-q4_k_m.gguf" ]; then
    echo "  Uploading Q4_K_M model (806MB)..."
    sshpass -p "${RPI_PASS}" scp -o StrictHostKeyChecking=no \
        "${MODEL_DIR}/gemma3-1b-q4_k_m.gguf" \
        "${RPI_USER}@${RPI_HOST}:${RPI_DIR}/data/models/"
    echo -e "${GREEN}✓ Q4_K_M uploaded${NC}"
else
    echo -e "${YELLOW}⚠️  Q4_K_M model not found, skipping${NC}"
fi

# Step 5: Deploy llama-cli binary
echo -e "${YELLOW}[5/8]${NC} Deploying llama-cli binary..."
if [ -f "../../build/bin/llama-cli" ]; then
    ssh_cmd "mkdir -p ${RPI_DIR}/bin"
    sshpass -p "${RPI_PASS}" scp -o StrictHostKeyChecking=no \
        "../../build/bin/llama-cli" \
        "${RPI_USER}@${RPI_HOST}:${RPI_DIR}/bin/"
    ssh_cmd "chmod +x ${RPI_DIR}/bin/llama-cli"
    echo -e "${GREEN}✓ llama-cli deployed${NC}"
else
    echo -e "${YELLOW}⚠️  llama-cli not found, Pi will need to build it${NC}"
fi

# Step 6: Install dependencies
echo -e "${YELLOW}[6/8]${NC} Installing Python dependencies on Pi..."
ssh_cmd "cd ${RPI_DIR} && python3 -m venv .venv && source .venv/bin/activate && pip install -q -r requirements.txt"
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 7: Install GPIO libraries (if on Pi)
echo -e "${YELLOW}[7/8]${NC} Installing GPIO libraries..."
ssh_cmd "cd ${RPI_DIR} && source .venv/bin/activate && pip install -q RPi.GPIO || echo 'GPIO install skipped'"
echo -e "${GREEN}✓ GPIO setup complete${NC}"

# Step 8: Initialize database
echo -e "${YELLOW}[8/8]${NC} Initializing EvoMemory database..."
ssh_cmd "cd ${RPI_DIR} && source .venv/bin/activate && python3 -c 'from core.evomemory import EvoMemoryDB; db = EvoMemoryDB(\"data/evomemory/neurons.db\"); print(\"✓ Database initialized\"); db.close()'"
echo -e "${GREEN}✓ Database initialized${NC}"

# Final checks
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}  ✅ DEPLOYMENT COMPLETE!${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Show status
echo "Remote files:"
ssh_cmd "cd ${RPI_DIR} && ls -lh data/models/*.gguf 2>/dev/null || echo 'No models found'"
echo ""

echo "Database stats:"
ssh_cmd "cd ${RPI_DIR} && source .venv/bin/activate && python3 -c 'from core.evomemory import EvoMemoryDB; db = EvoMemoryDB(\"data/evomemory/neurons.db\"); import json; print(json.dumps(db.get_stats(), indent=2)); db.close()'"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  Next steps:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. SSH into Pi:"
echo "   ssh ${RPI_USER}@${RPI_HOST}"
echo ""
echo "2. Start the server:"
echo "   cd ${RPI_DIR}"
echo "   source .venv/bin/activate"
echo "   python3 api/server.py"
echo ""
echo "3. Test the API:"
echo "   curl http://${RPI_HOST}:8000/stats"
echo ""
echo "4. Run examples:"
echo "   python3 examples/gpio_led_control.py"
echo "   python3 examples/rule_evolution_demo.py"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🎉 Ready to test Antonio Gemma3 Evo Q4 on Raspberry Pi! 🚀"
echo ""
