# 🚀 Deploy Manuale su Raspberry Pi 4 - Guida Step-by-Step

**Target**: Raspberry Pi 4 @ 192.168.1.24
**User**: o
**Password**: 207575

---

## ✅ STEP 1: Creare Tarball (FATTO!)

```bash
✓ Tarball creato: /tmp/antonio-evo-deploy.tar.gz (46 KB)
```

---

## 📤 STEP 2: Trasferire Codice sul Pi

**Sul tuo Mac**, apri un terminale e esegui:

```bash
# Trasferisci il tarball
scp /tmp/antonio-evo-deploy.tar.gz o@192.168.1.24:/home/o/

# Password: 207575
```

**Expected output**:
```
antonio-evo-deploy.tar.gz    100%   46KB   1.5MB/s   00:00
```

---

## 🔌 STEP 3: Connettiti al Pi

```bash
ssh o@192.168.1.24
# Password: 207575
```

**Dovresti vedere**:
```
o@raspberrypi:~ $
```

---

## 📂 STEP 4: Prepara Directory

**Sul Pi**, esegui:

```bash
# Crea directory
mkdir -p antonio-evo
cd antonio-evo

# Estrai tarball
tar -xzf ../antonio-evo-deploy.tar.gz

# Verifica
ls -la
```

**Dovresti vedere**:
```
api/
core/
data/
examples/
scripts/
tests/
README.md
requirements.txt
...
```

---

## 🐍 STEP 5: Setup Python Environment

**Sul Pi**:

```bash
# Crea virtual environment
python3 -m venv .venv

# Attiva venv
source .venv/bin/activate

# Dovresti vedere (.venv) nel prompt
# (.venv) o@raspberrypi:~/antonio-evo $

# Installa dipendenze
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected**: Installazione di FastAPI, uvicorn, pydantic, etc.

**Tempo stimato**: 2-3 minuti

---

## 🔌 STEP 6: Installa GPIO (opzionale, se hai LED)

**Sul Pi**:

```bash
# Installa RPi.GPIO
pip install RPi.GPIO
```

**Se errore** "Externally managed environment":
```bash
pip install RPi.GPIO --break-system-packages
```

---

## 🗄️ STEP 7: Inizializza Database

**Sul Pi**:

```bash
# Crea directory per data
mkdir -p data/evomemory/skills
mkdir -p data/models

# Inizializza database
python3 -c "
from core.evomemory import EvoMemoryDB
db = EvoMemoryDB('data/evomemory/neurons.db')
stats = db.get_stats()
print('✓ Database initialized')
print('Stats:', stats)
db.close()
"
```

**Expected output**:
```
✓ EvoMemory™ database initialized at data/evomemory/neurons.db
✓ Database initialized
Stats: {'neurons': 0, 'meta_neurons': 0, 'rules': 0, 'skills': 0, 'avg_confidence': 0.0}
```

---

## 🧪 STEP 8: Test Imports

**Sul Pi**:

```bash
python3 -c "
from core import *
print('✓ EvoMemory:', EvoMemoryDB)
print('✓ RAG-Lite:', RAGLite)
print('✓ Inference:', LlamaInference)
print('✓ Confidence:', ConfidenceScorer)
print('✓ Growth:', RuleGenerator)
print('✓ Tools:', ActionBroker)
print('✓ GPIO:', GPIOController)
print('')
print('🎉 All imports successful!')
"
```

**Expected**:
```
✓ EvoMemory: <class 'core.evomemory.schema.EvoMemoryDB'>
✓ RAG-Lite: <class 'core.evomemory.rag_lite.RAGLite'>
...
🎉 All imports successful!
```

---

## 🧬 STEP 9: Test EvoMemory

**Sul Pi**:

```bash
python3 examples/rule_evolution_demo.py
```

**Expected output**:
```
======================================================================
  Antonio Gemma3 Evo Q4 - Rule Evolution Demo
======================================================================

✓ Created 11 neurons
✓ Rules generated: 2
✓ RAG indexed 15 neurons

Rule 1:
  Text: Use high confidence for gpio_control tasks
  Trigger: skill_id:gpio_control
  Confidence threshold: 0.89
  Priority: 2

...

======================================================================
  Evolution complete! Check:
    - data/evomemory/neurons.db (SQLite)
    - data/evomemory/instinct.json (Generated rules)
======================================================================
```

**TEMPO**: ~2-5 secondi

---

## 🔗 STEP 10: Link Modelli

**Sul Pi**, trova dove sono i modelli esistenti:

```bash
# Cerca modelli
find /home/o -name "*.gguf" -type f 2>/dev/null
```

**Expected**:
```
/home/o/models/gemma3-1b-q4_0.gguf
/home/o/models/gemma3-1b-q4_k_m.gguf
```

**Crea symlink**:

```bash
# Link modelli nella directory antonio-evo
ln -s /home/o/models/gemma3-1b-q4_0.gguf data/models/
ln -s /home/o/models/gemma3-1b-q4_k_m.gguf data/models/

# Verifica
ls -lh data/models/
```

---

## 🔧 STEP 11: Link llama-cli

**Sul Pi**, trova llama-cli:

```bash
# Cerca llama-cli
find /home/o -name "llama-cli" -type f 2>/dev/null
```

**Expected**:
```
/home/o/llama.cpp/build/bin/llama-cli
```

**Crea symlink o usa path assoluto**:

```bash
# Opzione A: Symlink
mkdir -p bin
ln -s /home/o/llama.cpp/build/bin/llama-cli bin/llama-cli

# Opzione B: Nota il path per usarlo dopo
echo "llama-cli path: /home/o/llama.cpp/build/bin/llama-cli"
```

---

## 🧪 STEP 12: Test Inference (IMPORTANTE!)

**Sul Pi**, test con llama-cli diretto:

```bash
# Test veloce (usa il path corretto)
/home/o/llama.cpp/build/bin/llama-cli \
  -m data/models/gemma3-1b-q4_0.gguf \
  -p "Ciao! Come stai?" \
  -n 50 \
  -c 512 \
  -t 4
```

**Monitora**:
- Tokens/s (dovrebbe essere ~3.5-4.0 t/s)
- Temperatura CPU
- RAM usage

**Comando in parallelo (altro terminale SSH)**:

```bash
# Temperatura CPU
vcgencmd measure_temp

# RAM usage
free -h
```

---

## 🌐 STEP 13: Test FastAPI Server

**Sul Pi**:

```bash
# Modifica path llama-cli nel wrapper se necessario
# Oppure crea bin/llama-cli symlink (già fatto step 11)

# Avvia server
python3 api/server.py
```

**Expected**:
```
🚀 Starting Antonio Gemma3 Evo Q4...
✓ EvoMemory loaded: 15 neurons, 2 rules
✓ Loaded model: gemma3-1b-q4_0.gguf
✓ Server ready at http://localhost:8000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Dal Mac (altro terminale)**:

```bash
# Health check
curl http://192.168.1.24:8000/

# Stats
curl http://192.168.1.24:8000/stats | jq

# Chat test
curl -X POST http://192.168.1.24:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Ciao! Spiegami EvoMemory"}' | jq
```

---

## 📊 STEP 14: Benchmark Performance

**Sul Pi**, crea un file di test:

```bash
cat > benchmark.sh << 'EOF'
#!/bin/bash
echo "=== Antonio Gemma3 Evo Q4 - Benchmark ==="
echo ""

# Test 1: Inference speed
echo "Test 1: Inference Speed (Q4_0)"
time /home/o/llama.cpp/build/bin/llama-cli \
  -m data/models/gemma3-1b-q4_0.gguf \
  -p "Explain what is EvoMemory in 50 words" \
  -n 100 \
  -c 1024 \
  -t 4 2>&1 | grep "tokens/s"

echo ""
echo "Test 2: RAG Retrieval Speed"
time python3 -c "
from core.evomemory import EvoMemoryDB, NeuronStore, RAGLite
db = EvoMemoryDB('data/evomemory/neurons.db')
store = NeuronStore(db)
rag = RAGLite(store)
rag.index_neurons(max_neurons=100)
results = rag.retrieve('How to control LED?', top_k=5)
print(f'Retrieved {len(results)} neurons')
db.close()
"

echo ""
echo "Test 3: Rule Generation Speed"
time python3 -c "
from core.evomemory import EvoMemoryDB, NeuronStore
from core.growth import RuleGenerator
db = EvoMemoryDB('data/evomemory/neurons.db')
store = NeuronStore(db)
gen = RuleGenerator(store, db)
result = gen.auto_evolve(min_neurons=10)
print(f'Generated {result[\"rules_generated\"]} rules')
db.close()
"

echo ""
echo "=== Benchmark Complete ==="
EOF

chmod +x benchmark.sh
./benchmark.sh
```

---

## 🔌 STEP 15: Test GPIO (se hai LED)

**Hardware**: LED + resistor 220Ω su GPIO 17

**Sul Pi**:

```bash
sudo python3 -c "
from core.tools.gpio import GPIOController
import time

gpio = GPIOController(mode='BCM')
print('✓ GPIO initialized')

print('Test 1: LED blink...')
gpio.led_blink(17, times=5, interval=0.5)
print('✓ Blink complete')

print('Test 2: LED fade...')
gpio.led_fade(17, duration=3.0)
print('✓ Fade complete')

gpio.cleanup()
print('✓ GPIO cleanup done')
"
```

**Dovresti vedere**: LED lampeggia 5 volte, poi fade in/out

---

## ✅ CHECKLIST FINALE

Dopo aver completato tutti gli step, verifica:

- [ ] Codice estratto correttamente
- [ ] Virtual env creato
- [ ] Dipendenze installate
- [ ] Database inizializzato
- [ ] Rule evolution funziona (2 regole generate)
- [ ] Modelli linkati
- [ ] llama-cli funziona
- [ ] Inference speed: ~3.5-4 t/s
- [ ] FastAPI server risponde
- [ ] GPIO funziona (se testato)
- [ ] Temperatura CPU < 75°C

---

## 📊 RISULTATI DA DOCUMENTARE

Compila questi risultati:

```
=== RASPBERRY PI 4 BENCHMARK RESULTS ===

Hardware:
- Model: Raspberry Pi 4 4GB
- OS: Raspberry Pi OS (Debian Bookworm)
- CPU: Broadcom BCM2711 (Quad core Cortex-A72 @ 1.5GHz)

Performance:
- Inference (Q4_0): _____ tokens/s
- Inference (Q4_K_M): _____ tokens/s
- RAG retrieval (100 neurons): _____ ms
- Rule generation (15 neurons): _____ ms
- API response time: _____ ms

System:
- RAM usage (idle): _____ MB
- RAM usage (inference): _____ MB
- CPU temp (idle): _____ °C
- CPU temp (load): _____ °C

Status:
- All tests: PASS / FAIL
- Production ready: YES / NO
```

---

## 🎉 COMPLETATO!

Quando tutto funziona, hai:
- ✅ Antonio Gemma3 Evo Q4 running su Pi
- ✅ EvoMemory funzionante
- ✅ Rule Evolution testato
- ✅ FastAPI server online
- ✅ GPIO pronto (se hardware disponibile)

**Next**: Documenta i risultati in PI_TEST_CHECKLIST.md

---

**Need help?** Scrivi su GitHub Issues o contattami! 🚀
