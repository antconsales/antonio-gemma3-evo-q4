#!/usr/bin/env python3
"""
🎤 Antonio Voice System - Complete Voice Pipeline
Whisper.cpp (STT) → Antonio LLM → Piper-TTS (TTS)
"""

import subprocess
import tempfile
import os
import sys
import time
import wave
import pyaudio
import requests
from pathlib import Path

# ============================================================================
# CONFIG
# ============================================================================

WHISPER_DIR = Path.home() / "antonio-voice" / "whisper.cpp"
WHISPER_MODEL = WHISPER_DIR / "models" / "ggml-base.bin"
WHISPER_BIN = WHISPER_DIR / "main"

PIPER_DIR = Path.home() / "antonio-voice" / "piper"
PIPER_BIN = PIPER_DIR / "piper" / "piper"
PIPER_MODEL = PIPER_DIR / "models" / "it_IT-riccardo-x_low.onnx"

ANTONIO_API = "http://localhost:8000/chat"

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024
FORMAT = pyaudio.paInt16

# ============================================================================
# AUDIO FUNCTIONS
# ============================================================================

def record_audio(duration=5, silence_threshold=500, silence_duration=2.0):
    """
    Record audio from microphone
    Stops after silence or max duration
    """
    print("🎤 Registrando... (parla ora)")

    audio = pyaudio.PyAudio()

    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    frames = []
    silence_counter = 0
    silence_chunks = int(silence_duration * SAMPLE_RATE / CHUNK)

    try:
        for i in range(0, int(SAMPLE_RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)

            # Detect silence
            audio_data = int.from_bytes(data[:2], byteorder='little', signed=True)
            if abs(audio_data) < silence_threshold:
                silence_counter += 1
            else:
                silence_counter = 0

            # Stop if silence detected for too long
            if silence_counter > silence_chunks and len(frames) > 10:
                print("  (silenzio rilevato)")
                break

    except KeyboardInterrupt:
        print("\n⚠️  Interrotto")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save to temporary WAV file
    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

    with wave.open(temp_wav.name, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))

    print(f"✓ Registrazione salvata: {len(frames)} chunks")
    return temp_wav.name


def speech_to_text(audio_file):
    """
    Convert audio to text using Whisper.cpp
    """
    print("🗣️  Trascrivo con Whisper...")

    if not WHISPER_BIN.exists():
        raise FileNotFoundError(f"Whisper not found: {WHISPER_BIN}")

    if not WHISPER_MODEL.exists():
        raise FileNotFoundError(f"Whisper model not found: {WHISPER_MODEL}")

    try:
        result = subprocess.run(
            [
                str(WHISPER_BIN),
                "-m", str(WHISPER_MODEL),
                "-f", audio_file,
                "-l", "auto",  # Auto-detect language (IT/EN)
                "-t", "4",     # 4 threads
                "--no-timestamps"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"❌ Whisper error: {result.stderr}")
            return None

        # Parse output (Whisper prints to stderr)
        output = result.stderr

        # Extract transcribed text
        lines = output.split('\n')
        transcription = ""

        for line in lines:
            # Skip metadata lines
            if '[' in line or 'whisper_' in line or 'main:' in line:
                continue
            line = line.strip()
            if line:
                transcription += line + " "

        transcription = transcription.strip()

        if transcription:
            print(f"📝 Trascritto: {transcription}")
            return transcription
        else:
            print("⚠️  Nessun testo rilevato")
            return None

    except subprocess.TimeoutExpired:
        print("⏱️  Timeout Whisper")
        return None
    except Exception as e:
        print(f"❌ Errore Whisper: {e}")
        return None


def ask_antonio(text):
    """
    Send text to Antonio and get response
    """
    print(f"🤖 Chiedo ad Antonio...")

    try:
        response = requests.post(
            ANTONIO_API,
            json={
                "message": text,
                "voice_mode": True,  # Voice optimizations!
                "use_rag": False     # Faster for voice
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"💬 Antonio: {data['response']}")
            print(f"   (confidence: {data['confidence']:.2f}, {data['tokens_per_second']:.1f} t/s)")
            return data['response']
        else:
            print(f"❌ Antonio error: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("⏱️  Antonio timeout")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Antonio server")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def text_to_speech(text):
    """
    Convert text to speech using Piper-TTS
    """
    print("🔊 Genero audio con Piper...")

    if not PIPER_BIN.exists():
        raise FileNotFoundError(f"Piper not found: {PIPER_BIN}")

    if not PIPER_MODEL.exists():
        raise FileNotFoundError(f"Piper model not found: {PIPER_MODEL}")

    try:
        # Generate WAV file
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

        process = subprocess.Popen(
            [
                str(PIPER_BIN),
                "--model", str(PIPER_MODEL),
                "--output_file", temp_wav.name
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input=text, timeout=10)

        if process.returncode != 0:
            print(f"❌ Piper error: {stderr}")
            return None

        print(f"✓ Audio generato: {temp_wav.name}")
        return temp_wav.name

    except subprocess.TimeoutExpired:
        print("⏱️  Piper timeout")
        process.kill()
        return None
    except Exception as e:
        print(f"❌ Errore Piper: {e}")
        return None


def play_audio(audio_file):
    """
    Play audio file using aplay
    """
    print("▶️  Riproduco audio...")

    try:
        subprocess.run(
            ["aplay", audio_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30
        )
        print("✓ Riproduzione completata")

    except Exception as e:
        print(f"❌ Errore riproduzione: {e}")


# ============================================================================
# MAIN VOICE LOOP
# ============================================================================

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          🎤 Antonio Voice System - Raspberry Pi           ║")
    print("║              STT → LLM → TTS Pipeline                      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # Check dependencies
    print("🔍 Verifico componenti...")

    if not WHISPER_BIN.exists():
        print(f"❌ Whisper non trovato: {WHISPER_BIN}")
        print("   Esegui: bash ~/antonio-evo/scripts/install_whisper_pi.sh")
        sys.exit(1)

    if not PIPER_BIN.exists():
        print(f"❌ Piper non trovato: {PIPER_BIN}")
        print("   Esegui: bash ~/antonio-evo/scripts/install_piper_pi.sh")
        sys.exit(1)

    # Test Antonio connection
    try:
        status = requests.get("http://localhost:8000/", timeout=5)
        if status.status_code == 200:
            info = status.json()
            print(f"✓ Antonio: {info['name']}")
        else:
            raise Exception("Antonio not responding")
    except:
        print("❌ Antonio server non raggiungibile")
        print("   Avvia: cd ~/antonio-evo && python3 api/server.py")
        sys.exit(1)

    print("✓ Tutti i componenti pronti!")
    print()
    print("Comandi:")
    print("  - Premi INVIO per registrare")
    print("  - Dì 'esci' per uscire")
    print("  - CTRL+C per interrompere")
    print()
    print("═" * 60)

    conversation_count = 0

    while True:
        try:
            # Wait for user
            input("\n🎤 Premi INVIO per parlare... ")

            # Record audio
            audio_file = record_audio(duration=10, silence_duration=1.5)

            if not audio_file:
                continue

            # STT: Convert speech to text
            text = speech_to_text(audio_file)
            os.unlink(audio_file)  # Delete temp file

            if not text:
                print("⚠️  Non ho capito, riprova")
                continue

            # Check exit command
            if text.lower() in ['esci', 'exit', 'quit', 'basta']:
                print("👋 Ciao!")
                break

            # LLM: Ask Antonio
            start_time = time.time()
            response = ask_antonio(text)
            llm_time = time.time() - start_time

            if not response:
                print("⚠️  Antonio non ha risposto")
                continue

            # TTS: Convert response to speech
            speech_file = text_to_speech(response)

            if speech_file:
                # Play response
                play_audio(speech_file)
                os.unlink(speech_file)  # Delete temp file

            tts_time = time.time() - start_time - llm_time
            total_time = time.time() - start_time

            print(f"\n⏱️  Timing:")
            print(f"   LLM: {llm_time:.2f}s")
            print(f"   TTS: {tts_time:.2f}s")
            print(f"   Total: {total_time:.2f}s")

            conversation_count += 1
            print("─" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 Interrotto. Ciao!")
            break
        except Exception as e:
            print(f"\n❌ Errore: {e}")
            continue

    print(f"\n✓ Conversazioni completate: {conversation_count}")
    print("Grazie per aver usato Antonio Voice System!")


if __name__ == "__main__":
    main()
