# 👀🎙️ Antonio Voice + Eyes - Complete Architecture

**Hardware**: Waveshare ESP32-S3 DualEye LCD 1.28" + Raspberry Pi 5

---

## 🎯 Sistema Completo

```
┌─────────────────────────────────────────────────────────────┐
│                    ANTONIO FULL SYSTEM                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐          WiFi/MQTT          ┌──────────────────────┐
│   RASPBERRY PI 5     │◄──────────────────────────►│   ESP32-S3 DUALEYE   │
│                      │                             │                      │
│ ┌──────────────────┐ │                             │ ┌──────────────────┐ │
│ │  Antonio Brain   │ │                             │ │   Left Eye       │ │
│ │  (Gemma 3 1B)   │ │                             │ │  (240x240 IPS)   │ │
│ └──────────────────┘ │                             │ └──────────────────┘ │
│                      │                             │                      │
│ ┌──────────────────┐ │                             │ ┌──────────────────┐ │
│ │ Speech-to-Text   │ │        Commands:            │ │  Right Eye       │ │
│ │   (Whisper)      │ │     • Eye expression       │ │  (240x240 IPS)   │ │
│ └──────────────────┘ │     • Voice output         │ └──────────────────┘ │
│                      │     • Emotion sync         │                      │
│ ┌──────────────────┐ │                             │ ┌──────────────────┐ │
│ │ Text-to-Speech   │ │◄────── Audio Stream ───────┤ │  ES8311 Codec    │ │
│ │ (Piper/Coqui)   │ │                             │ │  + Speaker       │ │
│ └──────────────────┘ │                             │ └──────────────────┘ │
│                      │                             │                      │
│ ┌──────────────────┐ │──────► Audio Stream ───────►│ ┌──────────────────┐ │
│ │ Emotion Detector │ │                             │ │  ES7210 ADC      │ │
│ │  (from text)     │ │                             │ │  + Microphone    │ │
│ └──────────────────┘ │                             │ └──────────────────┘ │
│                      │                             │                      │
│ ┌──────────────────┐ │                             │ ┌──────────────────┐ │
│ │   EvoMemory      │ │                             │ │  Touch Input     │ │
│ │    Tools         │ │                             │ │  (CST816S)       │ │
│ └──────────────────┘ │                             │ └──────────────────┘ │
└──────────────────────┘                             └──────────────────────┘
```

---

## 🧠 Flow Completo

### 1️⃣ Voice Input Flow:

```
Microfono (ESP32) → ES7210 ADC → WiFi Stream → Raspberry Pi → Whisper STT → Testo
```

### 2️⃣ Antonio Processing:

```
Testo → Antonio Brain (Gemma 3) → Risposta + Emotion Detection → Comando Eyes + TTS
```

### 3️⃣ Voice Output Flow:

```
Raspberry Pi → Piper TTS (con tonalità) → Audio Stream → ESP32 → ES8311 Codec → Speaker
```

### 4️⃣ Eyes Expression Flow:

```
Emotion Detected → Comando MQTT → ESP32 → Eye Animation Renderer → Dual Display
```

---

## 🎭 Eye Expressions (Emozioni)

### Emozioni Disponibili:

| Emozione | Descrizione | Animazione | Use Case |
|----------|-------------|------------|----------|
| **NEUTRAL** | Normale, rilassato | Pupille centrate, blink occasionale | Idle state |
| **HAPPY** | Felice, sorridente | Pupille grandi, "sorriso" con forma | Risposta positiva |
| **THINKING** | Pensieroso | Pupille guardano su/lato, movimento lento | Sta elaborando |
| **SURPRISED** | Sorpreso | Pupille molto grandi, occhi aperti | Informazione nuova |
| **FOCUSED** | Concentrato | Pupille piccole, fissi su punto | Usa tool, calcola |
| **CONFUSED** | Confuso | Pupille piccole, movimento erratico | Non ha capito |
| **TIRED** | Stanco | Palpebre semi-chiuse, blink lento | Carico alto |
| **LISTENING** | In ascolto | Pupille che seguono "suono" | Durante voice input |
| **SPEAKING** | Sta parlando | Blink sincronizzato con voce | Durante TTS output |
| **ERROR** | Errore | Occhi rossi, lampeggiano | Errore di sistema |

### Componenti Grafici:

```
┌─────────────────────────┐
│   Singolo Occhio:       │
│                         │
│   ┌───────────────┐     │
│   │   ╭─────╮     │     │ ← Palpebra superiore (animabile)
│   │   │ ●   │     │     │ ← Pupilla (dimensione + posizione variabile)
│   │   ╰─────╯     │     │ ← Palpebra inferiore (animabile)
│   └───────────────┘     │
│                         │
│   + Sfondo iris colorato│
│   + Riflessi dinamici   │
│   + Vene/texture        │
└─────────────────────────┘
```

### Animazioni:

- **Blink**: Chiusura/apertura palpebre (100-200ms)
- **Look Around**: Movimento pupille in direzioni
- **Dilate**: Cambio dimensione pupille
- **Wink**: Chiusura un occhio solo
- **Squint**: Socchiudere occhi
- **Wide Open**: Apertura massima

---

## 🎤 Voice System

### Speech-to-Text (STT):

**Opzione 1: Whisper.cpp (Locale - Raccomandato)**
```bash
Modello: tiny.en o base.en
Dimensione: ~75MB (tiny) o ~140MB (base)
Latenza: ~1-2 secondi
Accuratezza: 85-90%
Privacy: ✅ Tutto locale
```

**Opzione 2: Vosk (Lightweight)**
```bash
Modello: vosk-model-small-it-0.22
Dimensione: ~45MB
Latenza: ~0.5-1 secondo
Accuratezza: 75-85%
Privacy: ✅ Tutto locale
```

**Opzione 3: Google Cloud STT (Cloud)**
```bash
Latenza: ~0.5 secondi
Accuratezza: 95%+
Privacy: ❌ Invia audio al cloud
```

### Text-to-Speech (TTS):

**Opzione 1: Piper TTS (Locale - Raccomandato)**
```bash
Modello: it_IT-riccardo-x_low
Dimensione: ~15MB
Qualità: Buona, naturale
Emotività: ⭐⭐⭐ (SSML per pitch/speed)
Latenza: ~0.5 secondi
```

**Opzione 2: Coqui TTS**
```bash
Modello: tts_models/it/mai_female/glow-tts
Qualità: Ottima
Emotività: ⭐⭐⭐⭐ (più controllo)
Latenza: ~1-2 secondi
```

**Opzione 3: ElevenLabs API (Cloud - Massima Qualità)**
```bash
Qualità: Eccellente, ultra-naturale
Emotività: ⭐⭐⭐⭐⭐ (controllo completo)
Latenza: ~1 secondo
Costo: ~$0.30 per 1000 caratteri
```

### Tonalità Vocali:

Con SSML (Speech Synthesis Markup Language):

```python
# Esempio Piper TTS con emozioni
{
    "HAPPY": {"rate": 1.1, "pitch": 1.2},      # Più veloce, più acuto
    "SAD": {"rate": 0.9, "pitch": 0.8},        # Più lento, più grave
    "EXCITED": {"rate": 1.3, "pitch": 1.3},    # Molto veloce, acuto
    "TIRED": {"rate": 0.8, "pitch": 0.9},      # Lento, leggermente grave
    "CONFUSED": {"rate": 0.95, "pitch": 1.1},  # Leggermente esitante
    "FOCUSED": {"rate": 1.0, "pitch": 1.0},    # Normale, chiaro
}
```

---

## 🔌 Comunicazione Pi ↔ ESP32

### Protocollo: MQTT (Raccomandato)

**Perché MQTT:**
- ✅ WiFi nativo su ESP32
- ✅ Low latency (~10-50ms)
- ✅ Bidirectional
- ✅ Topic-based (organizzazione chiara)
- ✅ QoS support

**MQTT Topics:**

```
antonio/eyes/expression     → Comando emozione occhi
antonio/eyes/position       → Posizione pupille
antonio/eyes/animation      → Animazione speciale
antonio/audio/stream/in     → Audio mic → Pi
antonio/audio/stream/out    → Audio Pi → speaker
antonio/status              → Status ESP32
antonio/config              → Configurazione
```

**Messaggio Esempio:**

```json
{
  "topic": "antonio/eyes/expression",
  "payload": {
    "emotion": "HAPPY",
    "duration": 2000,
    "intensity": 0.8,
    "transition": "smooth"
  }
}
```

### Alternativa: HTTP REST API

```
POST http://esp32.local/api/eyes
{
  "emotion": "THINKING",
  "duration": 1500
}
```

---

## 🎨 Emotion Detection

### Come Detectare Emozione dal Testo:

**Metodo 1: Rule-Based (Semplice, Veloce)**

```python
EMOTION_KEYWORDS = {
    "HAPPY": ["felice", "ottimo", "bene", "perfetto", "eccellente", "😊"],
    "CONFUSED": ["non capisco", "cosa intendi", "puoi spiegare", "?"],
    "THINKING": ["fammi pensare", "vediamo", "analizziamo", "consideriamo"],
    "SURPRISED": ["wow", "incredibile", "davvero", "!"],
    "ERROR": ["errore", "non funziona", "problema", "fallito"],
}

def detect_emotion(text):
    text_lower = text.lower()
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return emotion
    return "NEUTRAL"
```

**Metodo 2: Sentiment Analysis (Più Accurato)**

```python
from transformers import pipeline

sentiment = pipeline("sentiment-analysis",
                     model="nlptown/bert-base-multilingual-uncased-sentiment")

def detect_emotion_advanced(text):
    result = sentiment(text)[0]
    score = int(result['label'][0])  # 1-5 stars

    if score >= 4:
        return "HAPPY"
    elif score <= 2:
        return "SAD"
    else:
        return "NEUTRAL"
```

**Metodo 3: Dal Contesto di Antonio**

```python
# Antonio può includere emozione nella sua risposta
response_format = {
    "text": "Certo! 2+2 fa 4.",
    "emotion": "HAPPY",  # ← Antonio decide l'emozione
    "tools_used": []
}
```

---

## 📊 Performance Targets

| Componente | Target Latency | Actual |
|------------|----------------|--------|
| **Voice Input (STT)** | < 2s | TBD |
| **Antonio Processing** | < 3s | ~2s ✅ |
| **Voice Output (TTS)** | < 1s | TBD |
| **Eye Animation** | < 100ms | TBD |
| **MQTT Communication** | < 50ms | TBD |
| **Total User→Response** | < 6s | TBD |

---

## 🛠️ Tech Stack

### Raspberry Pi Software:

```yaml
Language: Python 3.11
Dependencies:
  - whisper.cpp (STT)
  - piper-tts (TTS)
  - paho-mqtt (Communication)
  - pyaudio (Audio I/O)
  - numpy (Audio processing)
  - ollama (Antonio brain)
```

### ESP32-S3 Firmware:

```yaml
Framework: Arduino / ESP-IDF
Language: C++
Libraries:
  - TFT_eSPI (Display driver)
  - PubSubClient (MQTT)
  - ArduinoJson (JSON parsing)
  - ESP32-audioI2S (Audio I/O)
  - lvgl (Graphics - optional)
```

---

## 🔧 Hardware Setup

### Connessioni:

```
ESP32-S3 DualEye:
├── Power: USB-C (5V) o batteria Li-Po 3.7V
├── WiFi: Connesso alla stessa rete del Raspberry Pi
├── Speaker: MX1.25 2PIN (8Ω 2W)
├── Microphone: Onboard (ES7210)
└── (Optional) Touch: I2C CST816S

Raspberry Pi 5:
├── Power: USB-C PD (27W)
├── Network: WiFi/Ethernet (stesso network ESP32)
├── (Optional) USB Mic: Se non usi ESP32 mic
└── (Optional) USB Speaker: Se non usi ESP32 speaker
```

### Audio Routing Options:

**Opzione A: Audio tutto su ESP32 (Raccomandato)**
```
User → ESP32 Mic → WiFi Stream → Pi (Whisper) → Text
Text → Pi (Piper) → WiFi Stream → ESP32 Speaker → User
```
✅ Tutto wireless
✅ ESP32 può essere portable
❌ Latenza WiFi (~50-100ms extra)

**Opzione B: Audio diretto su Pi**
```
User → Pi USB Mic → Pi (Whisper) → Text
Text → Pi (Piper) → Pi USB Speaker → User
ESP32 solo per Eyes
```
✅ Latenza minore
❌ Pi meno portable
❌ Cavi extra

---

## 📁 Project Structure

```
/home/pi/antonio/
├── brain/
│   ├── server.py                    # Antonio main server (UPDATED)
│   ├── emotion_detector.py          # NEW: Emotion detection
│   └── voice_handler.py              # NEW: Voice I/O manager
│
├── voice/
│   ├── stt/
│   │   ├── whisper_stt.py           # NEW: Whisper speech-to-text
│   │   └── models/                   # Whisper models
│   │       └── ggml-tiny.en.bin
│   │
│   └── tts/
│       ├── piper_tts.py             # NEW: Piper text-to-speech
│       └── models/
│           └── it_IT-riccardo-x_low.onnx
│
├── eyes/
│   ├── mqtt_bridge.py               # NEW: MQTT communication with ESP32
│   ├── emotion_mapper.py            # NEW: Emotion → Eye expression mapping
│   └── config.json                  # Eye animation configs
│
├── esp32/
│   └── antonio_eyes/                # NEW: ESP32 firmware
│       ├── antonio_eyes.ino         # Main firmware
│       ├── eye_renderer.cpp         # Eye graphics engine
│       ├── mqtt_handler.cpp         # MQTT client
│       ├── audio_stream.cpp         # Audio I/O
│       └── animations.h             # Eye animation definitions
│
├── config/
│   ├── voice_config.yaml
│   ├── eyes_config.yaml
│   └── mqtt_config.yaml
│
└── scripts/
    ├── setup_voice.sh               # NEW: Install voice deps
    ├── setup_esp32.sh               # NEW: Flash ESP32 firmware
    └── test_voice_eyes.sh           # NEW: Test complete system
```

---

## 🚀 Implementation Plan

### Phase 1: Voice Input (STT) ✅ First

**Tasks:**
1. Install Whisper.cpp on Pi
2. Create voice input service
3. Test mic → text pipeline
4. Integrate with Antonio server

**Test:**
```bash
python3 voice/stt/whisper_stt.py
# Parla: "Ciao Antonio"
# Output: "ciao antonio"
```

### Phase 2: Voice Output (TTS) ✅ Second

**Tasks:**
1. Install Piper TTS on Pi
2. Create voice output service with emotion control
3. Test text → audio → speaker
4. Add SSML for tonalità

**Test:**
```bash
python3 voice/tts/piper_tts.py "Ciao! Come stai?" --emotion HAPPY
# Speaker output: voce allegra
```

### Phase 3: Eye Animations ✅ Third

**Tasks:**
1. Setup ESP32 development environment
2. Create eye rendering engine
3. Implement 10 emotion animations
4. Test on dual displays

**Test:**
```bash
# Upload firmware to ESP32
arduino-cli upload -p /dev/ttyUSB0
# Eyes show HAPPY expression
```

### Phase 4: Communication ✅ Fourth

**Tasks:**
1. Setup MQTT broker on Pi (Mosquitto)
2. Implement MQTT bridge on Pi
3. Implement MQTT client on ESP32
4. Test bidirectional communication

**Test:**
```bash
mosquitto_pub -t antonio/eyes/expression -m '{"emotion":"THINKING"}'
# Eyes change to THINKING
```

### Phase 5: Emotion Detection ✅ Fifth

**Tasks:**
1. Create emotion detector from text
2. Integrate with Antonio responses
3. Map emotions to eye expressions + voice tone
4. Test emotion flow

**Test:**
```bash
# Antonio risponde: "Perfetto! 2+2 fa 4."
# Emotion detected: HAPPY
# Eyes: HAPPY
# Voice: Pitch 1.2, Rate 1.1
```

### Phase 6: Full Integration ✅ Final

**Tasks:**
1. Update Antonio server with voice + eyes
2. Create startup scripts
3. Full system testing
4. Performance optimization

**Test:**
```bash
# Completo voice conversation test
User (voice): "Quanto fa 1847 per 2935?"
Antonio (eyes): LISTENING → THINKING → FOCUSED
Antonio (voice): "Userò il calcolatore... il risultato è 5,421,245"
Antonio (eyes): HAPPY
```

---

## 🎯 Success Metrics

| Metric | Target | Priority |
|--------|--------|----------|
| **STT Accuracy** | > 85% | HIGH |
| **TTS Quality** | Natural voice | HIGH |
| **Eye Animation Smoothness** | 30+ FPS | MEDIUM |
| **Total Response Latency** | < 6s | HIGH |
| **Emotion Detection Accuracy** | > 75% | MEDIUM |
| **System Uptime** | > 99% | HIGH |
| **WiFi Latency** | < 100ms | MEDIUM |

---

## 💡 Future Enhancements

### V2 Features:

1. **Wake Word Detection**: "Hey Antonio" per attivare
2. **Multiple Voices**: Cambia voce in base a contesto
3. **Face Tracking**: Pupille seguono persona (con camera)
4. **Gesture Recognition**: Touch su occhi per comandi
5. **Music Sync**: Occhi ballano a ritmo musica
6. **Multi-Language**: IT/EN/ES voice support
7. **Offline Mode**: Tutto locale, no WiFi needed
8. **3D Eyes**: Effetti parallax per profondità

### V3 Advanced:

1. **GPT Vision**: ESP32 con camera, Antonio "vede"
2. **LipSync**: Sincronizzazione labiale (se aggiungi bocca display)
3. **Personality Modes**: Diverse personalità (serio, giocoso, ecc)
4. **Dream Mode**: Animazioni ambient quando idle
5. **Multi-Antonio**: Più ESP32, network di Antonio

---

## 📖 Quick Start (After Implementation)

```bash
# 1. Start MQTT broker
sudo systemctl start mosquitto

# 2. Start Antonio voice server
cd /home/pi/antonio
python3 brain/server.py --voice-enabled --eyes-enabled

# 3. Flash ESP32 (first time only)
cd esp32/antonio_eyes
arduino-cli upload -p /dev/ttyUSB0

# 4. Talk to Antonio!
# Speak: "Ciao Antonio, quanto fa 2+2?"
# Antonio eyes: LISTENING → THINKING → HAPPY
# Antonio voice: "Fa 4!"
```

---

## 🆘 Troubleshooting

### Voice not working:
```bash
# Check mic
arecord -l
# Check speaker
aplay -l
# Test MQTT
mosquitto_sub -t antonio/#
```

### Eyes not responding:
```bash
# Check ESP32 WiFi
ping esp32.local
# Check MQTT connection
mosquitto_pub -t antonio/eyes/expression -m '{"emotion":"HAPPY"}'
```

### High latency:
```bash
# Check network
ping -c 10 esp32.local
# Check Pi CPU
htop
# Reduce Whisper model size (use tiny instead of base)
```

---

**Version**: v0.7.0 (Voice + Eyes Edition)
**Status**: 📋 PLANNING COMPLETE - READY FOR IMPLEMENTATION
**Hardware Required**: ESP32-S3 DualEye + Raspberry Pi 5
**Estimated Dev Time**: 2-3 weeks

_"Antonio sta per avere voce ed emozioni!"_ 🎙️👀✨
