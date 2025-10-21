# 🧪 Raspberry Pi 4 Test Checklist

**Target**: Raspberry Pi 4 (4GB RAM)
**OS**: Raspberry Pi OS (Debian Bookworm)
**Date**: 2025-10-21

---

## 📋 Pre-Deployment Checklist

### Local Machine
- [ ] Models quantizzati pronti
  - [ ] `artifacts/gemma3-1b-q4_0.gguf` (720 MB)
  - [ ] `artifacts/gemma3-1b-q4_k_m.gguf` (806 MB)
- [ ] `llama-cli` compilato (`build/bin/llama-cli`)
- [ ] Antonio-evo code completo
- [ ] `sshpass` installato per deploy automatico

### Raspberry Pi
- [ ] Pi connesso alla rete
- [ ] SSH abilitato
- [ ] Spazio disco sufficiente (>3GB free)
- [ ] Python 3.8+ installato
- [ ] Git installato (opzionale)

---

## 🚀 Deployment Steps

### 1. Deploy Completo
```bash
cd antonio-evo
bash scripts/deploy_complete_to_pi.sh
```

**Expected output**:
```
✓ Connected to 192.168.1.24
✓ Code deployed
✓ Q4_0 uploaded
✓ Dependencies installed
✓ Database initialized
```

**Check**:
- [ ] Nessun errore durante deploy
- [ ] Tutti i file presenti su Pi
- [ ] Database creato correttamente

---

## 🧪 Test Suite

### Test 1: Basic System Check

**SSH to Pi**:
```bash
ssh o@192.168.1.24
cd antonio-evo
source .venv/bin/activate
```

**Run**:
```bash
python3 -c "from core import *; print('✓ All imports OK')"
```

**Expected**: `✓ All imports OK`

**Check**:
- [ ] No import errors
- [ ] All modules load correctly

---

### Test 2: EvoMemory Test

**Run**:
```bash
python3 -c "
from core.evomemory import EvoMemoryDB, Neuron, NeuronStore
db = EvoMemoryDB('data/evomemory/neurons.db')
store = NeuronStore(db)

n = Neuron('Test on Pi', 'Hello from Raspberry Pi!', confidence=0.9)
nid = store.save_neuron(n)
print(f'✓ Neuron {nid} saved')

stats = db.get_stats()
print(f'✓ Stats: {stats}')
db.close()
"
```

**Expected**:
```
✓ Neuron 1 saved
✓ Stats: {'neurons': 1, ...}
```

**Check**:
- [ ] Neuron saved successfully
- [ ] Stats retrieved
- [ ] Database file created

---

### Test 3: Inference Test (Q4_0)

**Run**:
```bash
python3 core/inference/llama_wrapper.py
```

**Input prompt**: `"Ciao! Come funziona la memoria evolutiva?"`

**Expected output**:
```
Output: [risposta del modello]
Stats: 50-100 tokens @ 3-4 t/s
Time: 15-30s
```

**Metrics to record**:
- [ ] Tokens/s: _________
- [ ] Time elapsed: _________
- [ ] Output quality: ⭐⭐⭐⭐⭐
- [ ] CPU temp before: _________
- [ ] CPU temp after: _________
- [ ] RAM usage: _________

---

### Test 4: RAG-Lite Performance

**Run**:
```bash
python3 examples/rule_evolution_demo.py
```

**Expected**:
```
✓ Created 11 neurons
✓ Rules generated: 2
✓ RAG indexed 15 neurons
```

**Metrics**:
- [ ] Indexing time: _________
- [ ] Retrieval time: _________
- [ ] Rule generation time: _________

**Check**:
- [ ] Rules saved to `instinct.json`
- [ ] BM25 retrieval works
- [ ] No memory errors

---

### Test 5: FastAPI Server

**Start server**:
```bash
python3 api/server.py
```

**Expected**:
```
✓ EvoMemory loaded: X neurons, Y rules
✓ Loaded model: gemma3-1b-q4_0.gguf
✓ Server ready at http://localhost:8000
```

**From another terminal (or laptop)**:
```bash
# Health check
curl http://192.168.1.24:8000/

# Stats
curl http://192.168.1.24:8000/stats

# Chat
curl -X POST http://192.168.1.24:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Ciao! Spiegami EvoMemory"}'
```

**Metrics**:
- [ ] Server boot time: _________
- [ ] Response time (chat): _________
- [ ] Tokens/s during chat: _________
- [ ] RAM usage (server running): _________
- [ ] CPU usage: _________

**Check**:
- [ ] All endpoints respond
- [ ] No timeout errors
- [ ] WebSocket works (optional)

---

### Test 6: GPIO Control (if hardware available)

**Hardware needed**:
- LED + resistor (220Ω) on GPIO 17
- Button on GPIO 27 (optional)

**Run**:
```bash
python3 -c "
from core.tools.gpio import GPIOController
gpio = GPIOController(mode='BCM')

# Test LED
gpio.led_blink(17, times=3, interval=0.5)
print('✓ LED blink test complete')

# Test fade
gpio.led_fade(17, duration=2.0)
print('✓ LED fade test complete')

gpio.cleanup()
"
```

**Expected**:
```
✓ LED blink test complete
✓ LED fade test complete
```

**Visual check**:
- [ ] LED blinks 3 times
- [ ] LED fades in/out smoothly
- [ ] No GPIO errors

---

### Test 7: Action Broker

**Run**:
```bash
python3 core/tools/broker.py
```

**Expected**:
```
Available tools:
  - fs.read: Read files from allowed directories
  - fs.write: Write files to allowed directories
  - gpio.write: Control GPIO pins (write)
  ...

Test fs.write:
  Success: True, Output: Written 25 bytes

Test fs.read:
  Success: True, Output: Hello from ActionBroker!
```

**Check**:
- [ ] Tool registry loaded
- [ ] fs.read/write works
- [ ] Audit log created
- [ ] GPIO tools detected (if on Pi)

---

### Test 8: Rule Evolution

**Run**:
```bash
python3 examples/rule_evolution_demo.py
```

**Expected**:
```
✓ Created 11 neurons
✓ Generated 2 rules, saved 2 new ones

Rule 1:
  Text: Use high confidence for gpio_control tasks
  Trigger: skill_id:gpio_control
  Confidence threshold: 0.89
```

**Check**:
- [ ] Rules generated
- [ ] `instinct.json` created
- [ ] Rules saved to DB
- [ ] No performance issues

**Metrics**:
- [ ] Time to analyze 100 neurons: _________
- [ ] Time to generate rules: _________

---

### Test 9: End-to-End Integration

**Scenario**: User chiede di controllare un LED via API

**Run server**:
```bash
python3 api/server.py
```

**From laptop**:
```bash
# 1. Ask about GPIO
curl -X POST http://192.168.1.24:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Come accendo il LED sul pin 17?"}' \
  | jq '.response, .confidence'

# 2. Give feedback
curl -X POST http://192.168.1.24:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"neuron_id": 1, "feedback": 1}'

# 3. Ask again (should use RAG)
curl -X POST http://192.168.1.24:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Ricordi come si accende un LED?", "use_rag": true}' \
  | jq '.rag_used, .response'
```

**Expected**:
```
Request 1: confidence > 0.7, risposta corretta
Request 2: feedback saved
Request 3: rag_used: true, risposta coerente con prima
```

**Check**:
- [ ] Neuron saved after first query
- [ ] Feedback applied
- [ ] RAG retrieves past neuron
- [ ] Response is coherent

---

### Test 10: Stress Test

**Run**:
```bash
# Generate 50 neurons
for i in {1..50}; do
  curl -s -X POST http://192.168.1.24:8000/chat \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test $i\"}" > /dev/null
  echo "Request $i done"
done
```

**Metrics**:
- [ ] Average response time: _________
- [ ] Max RAM usage: _________
- [ ] CPU throttling: YES / NO
- [ ] CPU temp max: _________
- [ ] Any errors: _________

**Check**:
- [ ] No crashes
- [ ] No memory leaks
- [ ] Temperature stays < 80°C
- [ ] Performance remains stable

---

## 📊 Performance Summary

### Target Metrics (Raspberry Pi 4)

| Metric | Target | Actual | Pass? |
|--------|--------|--------|-------|
| Inference speed (Q4_0) | >3.5 t/s | _____ | [ ] |
| Inference speed (Q4_K_M) | >3.0 t/s | _____ | [ ] |
| RAG retrieval time | <50ms | _____ | [ ] |
| Rule generation (100 neurons) | <5s | _____ | [ ] |
| API response time | <3s | _____ | [ ] |
| Memory usage (idle) | <800MB | _____ | [ ] |
| Memory usage (inference) | <1.5GB | _____ | [ ] |
| CPU temp (idle) | <60°C | _____ | [ ] |
| CPU temp (load) | <75°C | _____ | [ ] |

---

## 🐛 Issues Found

### Critical
- [ ] Issue 1: _______________________________________________
- [ ] Issue 2: _______________________________________________

### Minor
- [ ] Issue 1: _______________________________________________
- [ ] Issue 2: _______________________________________________

---

## ✅ Sign-Off

**All tests passed**: YES / NO

**Ready for production**: YES / NO

**Notes**:
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

**Tester**: _______________
**Date**: _______________
**Signature**: _______________

---

## 🚀 Next Steps After Testing

If all tests pass:
- [ ] Update README with actual benchmark results
- [ ] Create demo video
- [ ] Publish to GitHub
- [ ] Upload to HuggingFace
- [ ] Submit to Ollama
- [ ] Announce on Reddit/X

If tests fail:
- [ ] Document issues
- [ ] Fix critical bugs
- [ ] Re-test
- [ ] Update docs with limitations
