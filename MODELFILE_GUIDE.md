# 📄 Modelfile Guide - Antonio Gemma3 Evo Q4

## What is this?

The **Modelfile** is Antonio's "personality configuration" for Ollama. It defines:
- System prompt (core behavior and reasoning rules)
- Parameters (temperature, top-p, context size)
- Response template (Gemma 3 format)

This optimized version incorporates all learnings from production testing, including:
✅ Step-by-step math reasoning
✅ Written number recognition ("quattro" → 4)
✅ Bilingual support (IT/EN)
✅ Adaptive complexity handling
✅ Self-correction logic

---

## 🚀 How to Use

### Option 1: Pull from Ollama Registry (Easiest)

```bash
# Pull the pre-configured model
ollama pull antconsales/antonio-gemma3-evo-q4

# Run
ollama run antconsales/antonio-gemma3-evo-q4
```

### Option 2: Build Locally (For Customization)

```bash
# Clone the repo
git clone https://github.com/antconsales/antonio-gemma3-evo-q4.git
cd antonio-gemma3-evo-q4

# Create the model from Modelfile
ollama create antonio-local -f Modelfile

# Run your custom build
ollama run antonio-local
```

### Option 3: Modify and Rebuild

```bash
# Edit the Modelfile
nano Modelfile

# Make your changes (temperature, system prompt, etc.)

# Rebuild
ollama create antonio-custom -f Modelfile

# Test
ollama run antonio-custom
```

---

## 🎛️ Parameters Explained

### Current Settings (Optimized for Reasoning)

```dockerfile
PARAMETER temperature 0.7        # Balance creativity/determinism
PARAMETER top_p 0.9              # Nucleus sampling threshold
PARAMETER top_k 40               # Vocabulary limitation
PARAMETER repeat_penalty 1.1    # Prevent repetition
PARAMETER num_ctx 8192           # Context window size
```

### Tuning Guide

**For more creative responses:**
```dockerfile
PARAMETER temperature 0.9
PARAMETER top_p 0.95
```

**For more deterministic/factual:**
```dockerfile
PARAMETER temperature 0.5
PARAMETER top_p 0.85
PARAMETER top_k 20
```

**For longer conversations:**
```dockerfile
PARAMETER num_ctx 16384  # Use more RAM
```

---

## 🧪 Testing the Modelfile

### Test Suite

Run these tests after creating/modifying:

```bash
# Test 1: Simple greeting (should be fast, 1 sentence)
ollama run antonio-local "Ciao!"

# Test 2: Math reasoning (should show step-by-step)
ollama run antonio-local "Se un cane ha quattro zampe e ne perde una, quante ne ha?"

# Test 3: Bilingual (should respond in English)
ollama run antonio-local "What's your name?"

# Test 4: Code generation
ollama run antonio-local "Come scrivo una funzione Python per sommare due numeri?"

# Test 5: Logic problem
ollama run antonio-local "Un treno parte da Milano alle 9:00 e uno da Roma alle 9:30. Chi arriva prima se vanno alla stessa velocità?"
```

### Expected Outputs

**Test 1 (Simple):**
```
Ciao! Sono Antonio, un'IA locale che gira su dispositivi edge.
```

**Test 2 (Math Reasoning):**
```
Ragioniamo:
- Iniziali: 4 zampe
- Operazione: perde 1 zampa
- Calcolo: 4 - 1 = 3
Risposta: 3 zampe
```

**Test 3 (Bilingual):**
```
My name is Antonio, a local AI based on Gemma 3 1B running on edge devices.
```

---

## 🔧 Customization Examples

### 1. Change Personality

Edit the SYSTEM prompt:

```dockerfile
SYSTEM """You are Antonio, but with a more formal tone.
Always address the user as 'Sir/Madam' and use technical jargon."""
```

### 2. Add Custom Rules

Append to reasoning rules:

```dockerfile
SYSTEM """
...existing rules...

## CUSTOM RULES
- Always end responses with "🔧 Built on Pi"
- Prioritize open-source solutions
- Mention Raspberry Pi capabilities when relevant
"""
```

### 3. Optimize for Speed (Less Reasoning)

```dockerfile
PARAMETER temperature 0.5
PARAMETER top_k 20
PARAMETER num_ctx 4096

# Simplify system prompt
SYSTEM """You are Antonio. Be concise. Answer directly."""
```

---

## 📊 Benchmarking Your Modelfile

### Speed Test

```bash
# Time a simple question
time ollama run antonio-local "Ciao!" --verbose

# Time a complex question
time ollama run antonio-local "Se 5+3 fa 8, quanto fa 10-2?" --verbose
```

### Quality Test

Create a test script:

```bash
#!/bin/bash
# test_modelfile.sh

echo "=== Antonio Modelfile Quality Test ==="

# Math test
echo "Q: 4 zampe - 1 = ?"
ollama run antonio-local "Se un cane ha 4 zampe e ne perde 1, quante ne ha?" | grep -q "3" && echo "✓ PASS" || echo "✗ FAIL"

# Bilingual test
echo "Q: Bilingual support"
ollama run antonio-local "What's your name?" | grep -qi "antonio" && echo "✓ PASS" || echo "✗ FAIL"

echo "=== End Test ==="
```

---

## 🐛 Troubleshooting

### Issue: Model not reasoning step-by-step

**Cause:** System prompt not loaded correctly

**Fix:**
```bash
# Verify system prompt is active
ollama show antonio-local --modelfile

# Rebuild if needed
ollama create antonio-local -f Modelfile --force
```

### Issue: Wrong language responses

**Cause:** Language detection failing

**Fix:** Add explicit language instruction:
```bash
ollama run antonio-local "In italiano: come ti chiami?"
```

### Issue: Too slow on Raspberry Pi

**Reduce context window:**
```dockerfile
PARAMETER num_ctx 4096  # Instead of 8192
```

**Use lighter quantization:**
```dockerfile
FROM gemma3:1b-q4_0  # Instead of q4_k_m
```

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| v0.5.0 | Oct 21, 2025 | Added adaptive prompting logic, written numbers, bilingual templates |
| v0.4.0 | Oct 21, 2025 | Initial Modelfile with basic system prompt |

---

## 🔗 Resources

- **Main Repo:** https://github.com/antconsales/antonio-gemma3-evo-q4
- **HuggingFace:** https://huggingface.co/chill123/antonio-gemma3-evo-q4
- **Ollama Docs:** https://github.com/ollama/ollama/blob/main/docs/modelfile.md
- **Test Results:** See `docs/TEST_RESULTS_v0.5.0.md`

---

## 💡 Pro Tips

1. **Test before deployment:** Always run the test suite after modifying
2. **Version your Modelfiles:** Keep old versions for comparison
3. **Monitor performance:** Use `--verbose` flag to see token stats
4. **Iterate quickly:** Small changes → test → commit
5. **Share improvements:** Open PRs if you find better parameters!

---

## 🤝 Contributing

Found better parameters? Improved the system prompt?

1. Fork the repo
2. Modify `Modelfile`
3. Run test suite
4. Submit PR with benchmark results

We're always looking for improvements! 🚀

---

**"Il piccolo cervello che cresce insieme a te."** 🧠
