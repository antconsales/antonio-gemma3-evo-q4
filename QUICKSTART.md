# ⚡ Quick Start Guide — Antonio Gemma3 Evo Q4

**Get up and running in 5 minutes!**

---

## Option A: Ollama Only (Simplest)

Perfect if you just want to chat with the model.

### 1. Install Ollama

```bash
# Mac / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version
```

### 2. Pull the Model

```bash
# Q4_0 variant (recommended - faster, smaller)
ollama pull antconsales/antonio-gemma3-evo-q4

# Or Q4_K_M (better quality)
ollama pull antconsales/antonio-gemma3-evo-q4:q4_k_m
```

### 3. Create with EvoSystem Prompt

```bash
# Download Modelfile
curl -O https://raw.githubusercontent.com/antconsales/antonio-gemma3-evo-q4/main/antonio-evo/Modelfile.evo

# Create model
ollama create gemma3-evo -f Modelfile.evo
```

### 4. Chat!

```bash
ollama run gemma3-evo
```

**Test in Italian:**
```
>>> Ciao! Spiegami cos'è EvoMemory.
```

**Test in English:**
```
>>> Hello! What is EvoMemory?
```

✅ **Done!** The model runs 100% locally with the EvoSystem prompt.

---

## Option B: Full EvoLayer (Advanced)

Includes EvoMemory™, RAG, FastAPI server, and more.

### Prerequisites

- Python 3.8+
- Git
- llama.cpp (included in repo)

### 1. Clone the Repo

```bash
git clone https://github.com/antconsales/antonio-gemma3-evo-q4
cd antonio-gemma3-evo-q4
```

### 2. Build llama.cpp (if needed)

```bash
# Install CMake if not present
# Mac: brew install cmake
# Linux: sudo apt install cmake

cmake -B build
cmake --build build
```

### 3. Quantize Model

```bash
bash scripts/quantize_gemma.sh
```

This will:
- Download Gemma 3 1B from HuggingFace
- Convert to GGUF (fp16)
- Quantize to Q4_0 and Q4_K_M
- Save to `artifacts/`

**Time:** ~5-10 minutes

### 4. Install EvoLayer

```bash
cd antonio-evo
bash scripts/install.sh
```

This will:
- Create Python virtual environment
- Install dependencies
- Initialize SQLite database
- Link model files

### 5. Start the Server

```bash
source .venv/bin/activate
python3 api/server.py
```

Output:
```
🚀 Starting Antonio Gemma3 Evo Q4...
✓ EvoMemory loaded: 0 neurons, 0 rules
✓ Loaded model: gemma3-1b-q4_0.gguf
✓ Server ready at http://localhost:8000
```

### 6. Test the API

**Open browser:**
http://localhost:8000/docs

**Or use curl:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Ciao! Come funziona EvoMemory?"}'
```

**Response:**
```json
{
  "response": "EvoMemory è un sistema di memoria...",
  "confidence": 0.82,
  "confidence_label": "alta",
  "neuron_id": 1,
  "tokens_per_second": 3.67,
  "rag_used": false
}
```

### 7. Give Feedback

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"neuron_id": 1, "feedback": 1}'
```

### 8. Check Stats

```bash
curl http://localhost:8000/stats
```

**Response:**
```json
{
  "neurons_total": 5,
  "avg_confidence": 0.78,
  "uptime": "00:15:30"
}
```

✅ **Done!** EvoMemory is now learning from your conversations.

---

## Testing RAG-Lite

After a few conversations, test RAG retrieval:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Ricordi cosa ti ho chiesto prima su EvoMemory?",
    "use_rag": true
  }'
```

The model will retrieve relevant past neurons and use them as context!

---

## Raspberry Pi Setup

### 1. SSH into Pi

```bash
ssh pi@raspberrypi.local
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install build tools
sudo apt install -y cmake git python3-pip

# Install Ollama (optional)
curl -fsSL https://ollama.com/install.sh | sh
```

### 3. Clone and Build

```bash
git clone https://github.com/antconsales/antonio-gemma3-evo-q4
cd antonio-gemma3-evo-q4

# Build llama.cpp
cmake -B build
cmake --build build -j4  # Use all 4 cores
```

### 4. Download Pre-Quantized Model

Instead of quantizing on Pi (slow), download from HuggingFace:

```bash
cd antonio-evo/data/models

# Q4_0 (recommended)
wget https://huggingface.co/chill123/antonio-gemma3-smart-q4/resolve/main/gemma3-1b-q4_0.gguf

# Or Q4_K_M
wget https://huggingface.co/chill123/antonio-gemma3-smart-q4/resolve/main/gemma3-1b-q4_k_m.gguf
```

### 5. Install and Run

```bash
bash scripts/install.sh

source .venv/bin/activate
python3 api/server.py
```

### 6. Access from Another Device

```bash
# On Pi, note the IP address
hostname -I

# On your laptop
curl -X POST http://192.168.1.XX:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from my laptop!"}'
```

---

## Troubleshooting

### Model not found

```bash
# Check if model exists
ls -lh artifacts/*.gguf

# If missing, run quantization
bash scripts/quantize_gemma.sh
```

### llama-cli not found

```bash
# Build llama.cpp
cmake -B build
cmake --build build
```

### Port 8000 already in use

```bash
# Change port in api/server.py (line ~395)
uvicorn.run("server:app", host="0.0.0.0", port=8001)
```

### Import errors

```bash
# Activate venv
source .venv/bin/activate

# Reinstall deps
pip install -r requirements.txt
```

---

## Next Steps

- **Read the full README**: [README.md](README.md)
- **Explore the API**: http://localhost:8000/docs
- **Run tests**: `pytest tests/`
- **Star on GitHub**: https://github.com/antconsales/antonio-gemma3-evo-q4
- **Support the project**: https://www.paypal.com/donate/?business=58ML44FNPK66Y&currency_code=EUR

---

## Need Help?

- 🐛 **Bug reports**: Open an issue on GitHub
- 💬 **Questions**: Check FAQ in README.md
- 🤝 **Contribute**: PRs welcome!

---

**Happy hacking!** 🚀🧠
