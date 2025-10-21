# 🧠 Antonio Gemma3 Evo Q4

**The First Self-Learning Local AI for Raspberry Pi**
*Il primo modello AI locale auto-evolutivo per Raspberry Pi*

[![License: Gemma](https://img.shields.io/badge/License-Gemma-blue.svg)](https://ai.google.dev/gemma/terms)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4%2F5-red.svg)](https://www.raspberrypi.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Ready-green.svg)](https://ollama.com/antconsales/antonio-gemma3-evo-q4)

---

## 🌟 What Is This?

This is **not just** a quantized Gemma 3 model. It's a complete **self-learning AI system** that:

- 🧬 **Learns from every conversation** — Saves neurons with input, output, confidence, and mood
- 🔍 **RAG-Lite Memory** — Retrieves relevant past experiences using BM25 (no heavy deps)
- 🎯 **Self-evaluates** — Assigns confidence scores to every response
- 🌱 **Auto-evolves** — Generates new reasoning rules from accumulated knowledge
- 🔒 **100% Offline** — Runs completely local, zero telemetry
- 🌐 **Bilingual** — IT/EN auto-detection
- ⚡ **Fast** — 3.67 t/s on Raspberry Pi 4

> "Il piccolo cervello che cresce insieme a te" 🧠

---

## 🚀 Quick Start

### Option A: Ollama (Standalone Inference)

```bash
# Pull the model
ollama pull antconsales/antonio-gemma3-evo-q4

# Create with EvoSystem prompt
ollama create gemma3-evo -f Modelfile.evo

# Run!
ollama run gemma3-evo
>>> Ciao! Spiegami come funziona la tua memoria evolutiva.
```

### Option B: Full EvoLayer (with FastAPI Server)

```bash
# Clone the repo
git clone https://github.com/antconsales/antonio-gemma3-evo-q4
cd antonio-gemma3-evo-q4/antonio-evo

# Install
bash scripts/install.sh

# Start server
source .venv/bin/activate
python3 api/server.py

# Visit http://localhost:8000/docs
```

**Full EvoLayer includes:**
- EvoMemory™ (SQLite neuron storage)
- RAG-Lite (BM25 retrieval)
- Confidence scoring
- FastAPI REST + WebSocket
- (Coming soon) GPIO, Voice, Rule Regeneration

---

## 📊 Performance

Benchmarked on **Raspberry Pi 4 (4GB RAM)**:

| Variant | Speed | Size | Use Case |
|---------|-------|------|----------|
| **Q4_0** ⭐ | **3.67 t/s** | 720 MB | Default (faster, lighter) |
| **Q4_K_M** | 3.56 t/s | 806 MB | Better coherence in long chats |

**Tested on**: Raspberry Pi OS (Debian Bookworm), Ollama runtime

---

## 🧠 EvoMemory™ — How It Works

Every conversation creates a **neuron**:

```json
{
  "id": 123,
  "input_text": "Accendi il LED rosso",
  "output_text": "OK, attivo GPIO 17 su HIGH",
  "confidence": 0.85,
  "mood": "positive",
  "user_feedback": +1,
  "skill_id": "gpio_control",
  "timestamp": "2025-10-21T14:30:00Z"
}
```

**What happens next:**
1. Neuron is saved to SQLite database
2. RAG-Lite indexes it for future retrieval
3. If confidence < 0.4, the system asks for clarification
4. User feedback (👍/👎) updates neuron mood
5. Every 100 neurons → Rule Regeneration (auto-learning)

**No external APIs. No cloud. Just you and the Pi.**

---

## 💡 Key Features

### 1️⃣ Self-Learning
Unlike static models, Antonio **remembers** and **improves**:
- Saves successful responses as neurons
- Retrieves similar past experiences (RAG-Lite)
- Generates new reasoning rules from patterns

### 2️⃣ Confidence Scoring
Every response includes:
```json
{
  "confidence": 0.82,
  "confidence_label": "alta",
  "reasoning": "risposta dettagliata; trovate 1 espressioni di certezza"
}
```

If confidence < 0.4 → **"Non sono sicuro, puoi chiarire?"**

### 3️⃣ Privacy-First
- All data stays in local SQLite database
- No telemetry, no tracking, no cloud
- Perfect for medical, legal, personal use cases

### 4️⃣ Bilingual IT/EN
Auto-detects user language and responds accordingly.

```
User: "Ciao! Come stai?"
AI: "Ciao! Sto bene, grazie..."

User: "Hello! How are you?"
AI: "Hello! I'm doing well..."
```

### 5️⃣ Energy-Aware (Raspberry Pi)
Monitors CPU temperature and adjusts:
- `temp > 75°C` → reduce context to 512
- `temp > 70°C` → reduce to 768
- Prevents thermal throttling!

---

## 🎯 Use Cases

- **🏠 Offline Home Automation** — Control GPIO, sensors, IoT
- **🎙️ Voice Assistants** — Fast enough for real-time (3.67 t/s)
- **🔐 Privacy-Sensitive Apps** — Medical, legal, personal data
- **🌍 Bilingual Chatbots** — IT/EN customer support
- **📚 Educational Projects** — Learn AI on affordable hardware
- **🏭 Industrial IoT** — Offline inference for embedded systems

---

## 📦 What's Included

### Quantized Models
- `gemma3-1b-q4_0.gguf` (720 MB) — Recommended for Pi
- `gemma3-1b-q4_k_m.gguf` (806 MB) — Better quality

### EvoLayer (Python)
- **EvoMemory™**: SQLite neuron storage
- **RAG-Lite**: BM25 retrieval (no FAISS/ChromaDB)
- **Confidence Scorer**: Self-evaluation
- **FastAPI Server**: REST + WebSocket API
- **Llama.cpp Wrapper**: Optimized inference

### Coming Soon (v0.3+)
- Rule Regeneration (auto-evolution)
- Action Broker (GPIO, FS, media)
- Voice integration (Whisper.cpp + TTS)
- Social Learning (opt-in neuron sharing)

---

## 🛠️ API Endpoints

### `POST /chat`
```json
{
  "message": "Ciao! Spiegami EvoMemory",
  "use_rag": true
}
```

**Response:**
```json
{
  "response": "EvoMemory è un sistema...",
  "confidence": 0.85,
  "neuron_id": 42,
  "tokens_per_second": 3.67,
  "rag_used": true
}
```

### `POST /feedback`
```json
{
  "neuron_id": 42,
  "feedback": 1  // -1, 0, +1
}
```

### `GET /stats`
```json
{
  "neurons_total": 1234,
  "avg_confidence": 0.78,
  "uptime": "02:15:30"
}
```

### `WebSocket /ws`
Real-time chat with streaming.

---

## 📜 License

**Base Model**: [Google Gemma 3 1B IT](https://huggingface.co/google/gemma-3-1b-it)
**License**: [Gemma License](https://ai.google.dev/gemma/terms)

**Quantization, optimization, and EvoLayer™** by [Antonio](https://github.com/antconsales).

Please review and comply with Gemma License terms before use.

---

## 💖 Support the Project

This is a **free, open-source passion project** built with love for offline AI and edge computing.

If you find it useful, consider supporting development:

☕ **[Support Antonio Gemma on PayPal](https://www.paypal.com/donate/?business=58ML44FNPK66Y&no_recurring=0&item_name=Support+ethical%2C+local%2C+and+independent+AI.+Every+donation+helps+Antonio+Gemma+grow+and+evolve.+%F0%9F%92%99&currency_code=EUR)**

Your support helps:
- Keep the project maintained
- Add new features (GPIO, Voice, etc.)
- Test on more hardware
- Create tutorials and docs

**Donations are optional but deeply appreciated!** 🙏

---

## 🔗 Links

- **Ollama**: https://ollama.com/antconsales/antonio-gemma3-evo-q4
- **GitHub**: https://github.com/antconsales/antonio-gemma3-evo-q4
- **Model Card**: You're here! 👋
- **PayPal**: https://www.paypal.com/donate/?business=58ML44FNPK66Y&currency_code=EUR

---

## 🌟 Star the Repo!

If you like this project, give it a ⭐ on GitHub!

---

## 📊 Model Details

**Architecture**: Gemma3ForCausalLM
**Parameters**: 1B
**Context Length**: 1024 tokens (configurable)
**Vocabulary**: 262,144 tokens
**Quantization**: Q4_0, Q4_K_M (llama.cpp)
**Supported Platforms**: Raspberry Pi 4/5, Mac M1/M2, Linux ARM64/x86-64

---

## 🤔 FAQ

**Q: Does it really learn?**
A: Yes! Saves neurons with every conversation, retrieves them via RAG, and generates reasoning rules.

**Q: How is it different from Gemma 3?**
A: Adds EvoMemory™, RAG, confidence scoring, and auto-evolution. It's a learning **system**, not just a model.

**Q: Can I use it offline?**
A: 100%! No internet required.

**Q: Is my data safe?**
A: Absolutely. Everything stays in local SQLite. No telemetry.

**Q: Will it work on Pi 3?**
A: Probably slower. Optimized for Pi 4 (4GB) and Pi 5.

---

**Built with ❤️ for privacy and edge computing**
*Empowering local intelligence, one Raspberry Pi at a time.* 🧠🇮🇹

---

**Questions? Ideas? Feedback?**
💬 Open an issue on GitHub or reach out on X/Twitter!

**Want to contribute?**
🤝 PRs welcome! Check the README for dev setup.

**Enjoying the project?**
☕ [Support on PayPal](https://www.paypal.com/donate/?business=58ML44FNPK66Y&currency_code=EUR) | ⭐ Star on GitHub
