# 🎤 Antonio Voice System - Setup Guide

Sistema vocale completo per Raspberry Pi con:
- **Whisper.cpp** (STT - Speech to Text)
- **Antonio LLM** (con dual-model + voice optimizations)
- **Piper-TTS** (TTS - Text to Speech con voce italiana naturale)

---

## 🚀 Installazione Rapida

### Opzione 1: Installazione Automatica (CONSIGLIATA)

Sul Raspberry Pi, esegui:

```bash
cd ~/antonio-evo
bash scripts/setup_voice_complete.sh
```

Questo script installerà automaticamente:
- ✅ Whisper.cpp con modello base (74MB) per IT/EN
- ✅ Piper-TTS con voce italiana Riccardo
- ✅ Tutte le dipendenze Python
- ✅ Script voice pipeline completo

**Tempo stimato**: 15-20 minuti (compilazione Whisper.cpp)

---

### Opzione 2: Installazione Manuale

#### Step 1: Installa Whisper.cpp (STT)

```bash
cd ~/antonio-evo
bash scripts/install_whisper_pi.sh
```

#### Step 2: Installa Piper-TTS (TTS)

```bash
bash scripts/install_piper_pi.sh
```

#### Step 3: Installa dipendenze Python

```bash
cd ~/antonio-evo
source .venv/bin/activate
pip install pyaudio requests
```

---

## 🎙️ Utilizzo

### Avvia Antonio Voice System

**Terminale 1** - Avvia Antonio Server:
```bash
cd ~/antonio-evo
source .venv/bin/activate
python3 api/server.py
```

**Terminale 2** - Avvia Voice System:
```bash
cd ~/antonio-evo
source .venv/bin/activate
python3 antonio_voice.py
```

### Come funziona:

1. **Premi INVIO** per iniziare a parlare
2. **Parla** (il sistema rileva automaticamente il silenzio)
3. **Antonio elabora** la richiesta con voice_mode ottimizzato
4. **Ascolta la risposta** vocale

Dì **"esci"** per terminare.

---

## ⚡ Performance Attese

| Componente | Latenza | Note |
|------------|---------|------|
| **Registrazione** | ~2s | Rilevamento automatico silenzio |
| **Whisper STT** | ~0.5-1s | Modello base, 4 threads |
| **Antonio LLM** | ~2-3s | Voice mode (50 tokens max) |
| **Piper TTS** | ~0.1s | Voce italiana Riccardo |
| **Riproduzione** | ~2s | Dipende dalla lunghezza |
| **TOTALE** | ~5-8s | End-to-end |

---

## 🔧 Test Componenti Individuali

### Test Piper-TTS (voce)
```bash
~/antonio-voice/piper/speak.sh "Ciao, sono Antonio!"
```

### Test Whisper.cpp (STT)
```bash
cd ~/antonio-voice/whisper.cpp
./main -m models/ggml-base.bin -f samples/jfk.wav
```

### Test Antonio API
```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "ciao", "voice_mode": true}'
```

---

## 📂 Struttura File

```
~/antonio-evo/
├── antonio_voice.py              # Voice pipeline principale
├── api/server.py                  # Antonio server (già attivo)
└── scripts/
    ├── install_whisper_pi.sh      # Installa Whisper.cpp
    ├── install_piper_pi.sh        # Installa Piper-TTS
    └── setup_voice_complete.sh    # Setup automatico completo

~/antonio-voice/
├── whisper.cpp/                   # Whisper.cpp + modelli
│   ├── main                       # Binary STT
│   └── models/ggml-base.bin      # Modello base (74MB)
└── piper/                         # Piper-TTS
    ├── piper/piper                # Binary TTS
    ├── models/it_IT-riccardo-x_low.onnx  # Voce italiana
    └── speak.sh                   # Script rapido TTS
```

---

## 🎯 Ottimizzazioni Voice Mode

Il sistema Antonio è già ottimizzato per voice:

### Automatic Query Routing
- **Query semplici** → Fast model (antconsales/antonio-gemma3-evo-q4)
- **Query complesse** → Tool model (antonio-tools)

### Voice Mode Optimizations
Quando `voice_mode: true`:
- ✅ RAG disabilitato per query semplici (-200ms)
- ✅ Context ridotto: 512 vs 1024 tokens
- ✅ Max tokens: 50 vs 256 (risposte concise)
- ✅ Prompt ultra-conciso (max 2-3 frasi)

Risultato: **~2-3s** invece di ~15s! 🚀

---

## 🔊 Configurazione Audio

### Dispositivi Audio Consigliati

**Microfono**: USB o integrato Pi
```bash
# Lista dispositivi disponibili
arecord -l
```

**Speaker**: USB, HDMI o jack 3.5mm
```bash
# Test speaker
speaker-test -t wav -c 2
```

### Configurazione ALSA

Se necessario, configura dispositivo di default:
```bash
# Edita
nano ~/.asoundrc

# Aggiungi (sostituisci con i tuoi device)
pcm.!default {
    type hw
    card 1
}
```

---

## 🐛 Troubleshooting

### Whisper non trova il modello
```bash
cd ~/antonio-voice/whisper.cpp
bash ./models/download-ggml-model.sh base
```

### Piper voce robotica
Scarica modello quality "medium" invece di "x_low":
```bash
cd ~/antonio-voice/piper/models
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/riccardo/medium/it_IT-riccardo-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/riccardo/medium/it_IT-riccardo-medium.onnx.json
```

### Antonio server non risponde
```bash
# Verifica che sia attivo
ps aux | grep "python.*server.py"

# Riavvia
cd ~/antonio-evo
source .venv/bin/activate
python3 api/server.py
```

### PyAudio errors
```bash
# Reinstalla con dipendenze corrette
sudo apt-get install portaudio19-dev python3-pyaudio
pip install --force-reinstall pyaudio
```

---

## 🎉 Next Steps

### Miglioramenti Futuri

1. **Wake Word Detection**: Aggiungere "Hey Antonio"
2. **Streaming TTS**: Audio in tempo reale mentre genera
3. **Voice Activity Detection**: Migliore rilevamento inizio/fine speech
4. **Multi-language**: Selezione automatica lingua
5. **ESP32 Integration**: Collegare hardware ESP32-S3 DualEye

---

## 📊 Statistiche Performance

Il sistema logga automaticamente:
- ⏱️ Latenza LLM
- ⏱️ Latenza TTS
- ⏱️ Totale end-to-end
- 🎯 Tokens generati
- ⚡ Velocità (tokens/s)

---

## ✅ Checklist Post-Installazione

- [ ] Whisper.cpp compilato e funzionante
- [ ] Modello base scaricato (74MB)
- [ ] Piper-TTS installato
- [ ] Voce italiana Riccardo scaricata
- [ ] PyAudio installato
- [ ] Antonio server attivo su :8000
- [ ] Microfono USB collegato
- [ ] Speaker funzionante
- [ ] Test "speak.sh" funziona
- [ ] antonio_voice.py eseguibile

---

**Enjoy talking with Antonio!** 🎤🤖🔊
