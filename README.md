# 🧠 Antonio Gemma3 Evo Q4

**The first self-learning, local, and auto-evolutionary small language model**
*Il primo modello linguistico leggero, locale e auto-evolutivo*

[![License: Gemma](https://img.shields.io/badge/License-Gemma-blue.svg)](https://ai.google.dev/gemma/terms)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4%2F5-red.svg)](https://www.raspberrypi.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Ready-green.svg)](https://ollama.com)

---

## 🌟 What Makes It Special

Antonio Gemma3 Evo Q4 is not just another quantized LLM. It's a **micro-intelligence** that:

- 🧬 **Learns from every conversation** — Saves "neurons" with input, output, confidence, and mood
- 🔍 **RAG-Lite Memory** — Retrieves past experiences using BM25 (no heavy dependencies)
- 🎯 **Self-evaluates** — Assigns confidence scores (0-1) to every response
- 🌱 **Auto-evolves** — Generates new reasoning rules from accumulated neurons
- 🔒 **100% Offline** — Runs completely local on Raspberry Pi 4 (4GB RAM)
- 🌐 **Bilingual** — Auto-detects IT/EN and responds in the same language
- ⚡ **Fast** — 3.32 tokens/s sustained on Pi 4 with Q4_K_M quantization

> "The little brain that grows with you" 🧠

📊 **[View Complete Benchmark Report](BENCHMARK_REPORT.md)** — Performance, reliability, and stability metrics

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│  Antonio Gemma3 Evo Q4 - Evolution Layer    │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │ EvoMemory™   │◄────►│  RAG-Lite       │ │
│  │ (SQLite)     │      │  BM25 Search    │ │
│  └──────────────┘      └─────────────────┘ │
│         ▲                      ▲            │
│         │                      │            │
│  ┌──────┴──────────────────────┴──────────┐ │
│  │    Inference Engine (llama.cpp)        │ │
│  │    • Q4_0 / Q4_K_M                     │ │
│  │    • Optimized for Pi 4                │ │
│  └────────────────────────────────────────┘ │
│         ▲                      │            │
│         │                      ▼            │
│  ┌──────┴─────────┐    ┌──────────────────┐ │
│  │ Action Broker  │    │  Confidence      │ │
│  │ (MCP-ready)    │    │  Auto-Eval       │ │
│  └────────────────┘    └──────────────────┘ │
│                                             │
│  FastAPI Server (REST + WebSocket)         │
└─────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- llama.cpp (already included in parent directory)
- Raspberry Pi 4/5 with 4GB RAM (or Mac/Linux for development)

### 1. Installation

```bash
cd antonio-evo
bash scripts/install.sh
```

This will:
- Create virtual environment
- Install dependencies
- Initialize SQLite database
- Link model files from `../artifacts/`

### 2. Download/Quantize Model

If you don't have the model yet:

```bash
cd ..
bash scripts/quantize_gemma.sh
```

This creates:
- `artifacts/gemma3-1b-q4_0.gguf` (720 MB, faster)
- `artifacts/gemma3-1b-q4_k_m.gguf` (806 MB, better quality)

### 3. Start the Server

```bash
source .venv/bin/activate
python3 api/server.py
```

Visit: **http://localhost:8000/docs** for interactive API documentation

### 4. Chat!

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Ciao! Come funziona la tua memoria evolutiva?"}'
```

Response:
```json
{
  "response": "La mia memoria evolutiva funziona attraverso neuroni che salvano input, output, e confidenza...",
  "confidence": 0.82,
  "confidence_label": "alta",
  "reasoning": "risposta dettagliata; trovate 1 espressioni di certezza",
  "neuron_id": 42,
  "tokens_per_second": 3.67,
  "rag_used": true
}
```

---

## 💡 Core Features

### 1️⃣ EvoMemory™ — Living Memory

Every conversation creates a **neuron**:

```python
{
  "id": 123,
  "input_text": "Accendi il LED rosso",
  "output_text": "OK, attivo GPIO 17 su HIGH",
  "confidence": 0.85,
  "mood": "positive",
  "user_feedback": +1,  # 👍 from user
  "skill_id": "gpio_control",
  "timestamp": "2025-10-21T14:30:00Z"
}
```

**Features:**
- Auto-pruning of low-confidence old neurons
- Neuron compression (similar patterns → meta-neurons)
- Context-aware retrieval via hash matching

### 2️⃣ RAG-Lite — Smart Retrieval

Uses **BM25** (pure Python) to retrieve relevant past experiences:

```python
# Query: "Come controllo un LED?"
# Retrieves:
# - "Accendi il LED rosso" → score: 0.87
# - "Spegni il LED" → score: 0.72
```

No FAISS, no ChromaDB, no heavy dependencies!

### 3️⃣ Confidence Scoring — Self-Awareness

Every response gets a confidence score (0-1):

- **Pattern analysis**: "non sono sicuro", "forse" → lower confidence
- **Length check**: too short → suspicious
- **Repetition detection**: hallucination indicator
- **Context matching**: prompt vs output coherence

### 4️⃣ Auto-Evolution (Coming Soon)

Every 100 interactions:
1. Analyze neurons
2. Group similar patterns
3. Generate new reasoning rules
4. Update `instinct.json`

Example rule:
```json
{
  "rule": "never_claim_internet_when_offline",
  "trigger_pattern": "detect_hallucination",
  "priority": 1
}
```

### 5️⃣ Energy-Aware Inference

Monitors CPU temperature and adjusts:

```python
if cpu_temp > 75°C:
    reduce_context_to(512)
    switch_to_Q4_0()  # faster quantization
```

Prevents thermal throttling on Raspberry Pi!

---

## 📊 API Endpoints

### `POST /chat`

Main chat endpoint with RAG support.

**Request:**
```json
{
  "message": "What is EvoMemory?",
  "use_rag": true,
  "skill_id": "conversation"
}
```

**Response:**
```json
{
  "response": "EvoMemory is a SQLite-based system that stores...",
  "confidence": 0.78,
  "confidence_label": "high",
  "neuron_id": 456,
  "tokens_per_second": 3.67,
  "rag_used": true
}
```

### `POST /feedback`

Submit user feedback on a neuron.

```json
{
  "neuron_id": 456,
  "feedback": 1  // -1 (bad), 0 (neutral), +1 (good)
}
```

### `GET /stats`

System statistics.

```json
{
  "neurons_total": 1234,
  "meta_neurons": 42,
  "rules_active": 8,
  "avg_confidence": 0.73,
  "uptime": "02:15:30"
}
```

### `GET /neurons/recent?limit=10`

Get recent neurons.

### `WebSocket /ws`

Real-time chat with streaming support.

---

## 🛠️ Development

### Project Structure

```
antonio-evo/
├── core/
│   ├── evomemory/
│   │   ├── schema.py          # SQLite database schema
│   │   ├── neuron_store.py    # CRUD operations
│   │   └── rag_lite.py        # BM25 retrieval
│   ├── inference/
│   │   ├── llama_wrapper.py   # llama.cpp integration
│   │   └── confidence.py      # Self-evaluation
│   ├── tools/                 # (Coming soon)
│   │   ├── broker.py          # Action Broker
│   │   └── gpio/              # Raspberry Pi GPIO
│   └── growth/                # (Coming soon)
│       └── rule_generator.py  # Auto-evolution
├── api/
│   └── server.py              # FastAPI server
├── data/
│   ├── evomemory/
│   │   ├── neurons.db         # SQLite database
│   │   └── skills/            # Skill modules
│   └── models/                # Model symlinks
├── scripts/
│   └── install.sh             # Installation script
├── tests/                     # Unit tests
└── requirements.txt
```

### Running Tests

```bash
pytest tests/
```

### Adding a New Skill

1. Create skill definition in `data/evomemory/skills/my_skill.json`:

```json
{
  "id": "my_skill",
  "name": "My Awesome Skill",
  "description": "What it does",
  "enabled": true
}
```

2. Tag neurons with `skill_id="my_skill"` when saving

3. Query skill-specific neurons:

```python
neurons = store.get_recent_neurons(skill_id="my_skill")
```

---

## 🎯 Use Cases

- **🏠 Offline Home Automation** — Control GPIO, sensors, actuators
- **🎙️ Voice Assistants** — Fast enough for real-time speech (3.67 t/s)
- **🔐 Privacy-First AI** — Medical, legal, personal data (100% local)
- **🌍 Bilingual Chatbots** — Customer support, documentation (IT/EN)
- **📚 Educational Projects** — Learn AI/ML on affordable hardware
- **🏭 Embedded Systems** — Industrial applications requiring offline inference

---

## 📈 Roadmap

- [x] **v0.1** — Core EvoMemory + RAG + Confidence
- [x] **v0.2** — FastAPI server + WebSocket
- [ ] **v0.3** — Rule Regeneration system
- [ ] **v0.4** — Action Broker + Tool Registry (MCP-ready)
- [ ] **v0.5** — GPIO control for Raspberry Pi
- [ ] **v0.6** — Voice integration (Whisper.cpp + TTS)
- [ ] **v0.7** — Social Learning (opt-in neuron sharing)
- [ ] **v0.8** — Multi-model support (Qwen, Phi, Mistral)

---

## 🤝 Contributing

Contributions are welcome! This is an **open-source passion project**.

Ideas? Bugs? Feature requests?
Open an issue or PR on GitHub!

---

## 📜 License

This model is a **derivative work** of [Google's Gemma 3 1B](https://huggingface.co/google/gemma-3-1b-it).

**License**: Gemma License
Please review and comply with the [Gemma License Terms](https://ai.google.dev/gemma/terms).

**Quantization, optimization, and EvoLayer** by [Antonio](https://github.com/antconsales).

---

## 🔗 Links

- **Ollama**: https://ollama.com/antconsales/antonio-gemma3-evo-q4
- **Hugging Face**: https://huggingface.co/chill123/antonio-gemma3-evo-q4
- **GitHub**: https://github.com/antconsales/antonio-gemma3-evo-q4

---

## 🌟 Star History

If you like this project, give it a ⭐ on GitHub!

---

**Built with ❤️ for offline AI and edge computing**
*Empowering local intelligence, one Raspberry Pi at a time.* 🧠🇮🇹

---

## 💬 FAQ

**Q: Can it really learn from conversations?**
A: Yes! Every chat saves a neuron with input, output, confidence, and user feedback. RAG retrieves relevant neurons for future queries.

**Q: How is it different from regular Gemma 3?**
A: It adds EvoMemory™, RAG, confidence scoring, and auto-evolution. It's not just inference—it's a learning system.

**Q: Will it work on Raspberry Pi 3?**
A: Probably, but slower. Optimized for Pi 4 (4GB) and Pi 5.

**Q: Can I use it offline?**
A: 100%! No internet required. All inference and learning happens locally.

**Q: Is my data safe?**
A: Absolutely. Everything stays in your SQLite database. No telemetry, no tracking, no cloud.

**Q: Can I add custom tools (GPIO, sensors, etc.)?**
A: Coming in v0.4! Action Broker with MCP compatibility.

**Q: Does it support other languages?**
A: Currently IT/EN. More languages can be added via system prompt customization.

---

**Questions? Ideas? Let's chat!** 💬
