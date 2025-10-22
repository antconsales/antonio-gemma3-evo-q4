#!/usr/bin/env python3
"""
🎤 Antonio Voice Client - Mac Edition
Client vocale per parlare con Antonio sul Raspberry Pi
"""

import speech_recognition as sr
import pyttsx3
import requests
import json
import sys
from datetime import datetime

# ============================================================================
# CONFIG
# ============================================================================

ANTONIO_API = "http://raspberrypi.local:8000/chat"
VOICE_MODE = True  # Abilita ottimizzazioni voice

# ============================================================================
# SETUP
# ============================================================================

# Text-to-Speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 175)  # Velocità voce (default 200)
tts_engine.setProperty('volume', 1.0)  # Volume (0.0-1.0)

# Seleziona voce italiana se disponibile
voices = tts_engine.getProperty('voices')
italian_voice = None
for voice in voices:
    if 'italian' in voice.name.lower() or 'alice' in voice.name.lower():
        italian_voice = voice.id
        break

if italian_voice:
    tts_engine.setProperty('voice', italian_voice)
    print(f"✓ Voce italiana selezionata")

# Speech recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 4000  # Sensibilità microfono
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8  # Pausa per fine frase (secondi)

# ============================================================================
# FUNCTIONS
# ============================================================================

def speak(text: str):
    """Leggi testo ad alta voce"""
    print(f"\n🤖 Antonio: {text}\n")
    tts_engine.say(text)
    tts_engine.runAndWait()


def listen() -> str:
    """Ascolta dal microfono e converti a testo"""
    with sr.Microphone() as source:
        print("\n🎤 Ascolto... (parla ora)")

        # Calibrazione rumore ambientale
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("⏳ Elaboro...")

            # Prova italiano, poi inglese
            try:
                text = recognizer.recognize_google(audio, language="it-IT")
                print(f"📝 Hai detto: {text}")
                return text
            except sr.UnknownValueError:
                # Prova inglese
                try:
                    text = recognizer.recognize_google(audio, language="en-US")
                    print(f"📝 You said: {text}")
                    return text
                except:
                    print("❌ Non ho capito. Riprova.")
                    return None

        except sr.WaitTimeoutError:
            print("⏱️ Timeout - nessun audio rilevato")
            return None
        except Exception as e:
            print(f"❌ Errore: {e}")
            return None


def ask_antonio(message: str) -> dict:
    """Invia messaggio ad Antonio e ricevi risposta"""
    try:
        response = requests.post(
            ANTONIO_API,
            json={
                "message": message,
                "voice_mode": VOICE_MODE,
                "use_rag": False  # Disabilita RAG per voice (più veloce)
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Errore API: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("⏱️ Timeout - Antonio sta pensando troppo...")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Impossibile connettersi al Raspberry Pi")
        print("   Verifica che Antonio sia in esecuzione su raspberrypi.local:8000")
        return None
    except Exception as e:
        print(f"❌ Errore: {e}")
        return None


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          🎤 Antonio Voice Client - Mac Edition            ║")
    print("║                 Parla con Antonio!                         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # Test connessione
    print("🔍 Controllo connessione al Raspberry Pi...")
    try:
        status = requests.get("http://raspberrypi.local:8000/", timeout=5)
        if status.status_code == 200:
            info = status.json()
            print(f"✓ Connesso: {info['name']}")
            print(f"  Mode: {info['mode']}")
            print(f"  Models: {info['models']['fast']} + {info['models']['tools']}")
        else:
            print("⚠️ Server raggiungibile ma risponde male")
    except:
        print("❌ ERRORE: Impossibile raggiungere raspberrypi.local:8000")
        print("\nVerifica che:")
        print("  1. Il Raspberry Pi sia acceso e connesso alla rete")
        print("  2. Antonio server sia in esecuzione (python3 api/server.py)")
        print("  3. Il Mac e Pi siano sulla stessa rete")
        sys.exit(1)

    print()
    print("Comandi:")
    print("  - Parla normalmente per chattare con Antonio")
    print("  - Dì 'esci' o 'quit' per uscire")
    print("  - Premi CTRL+C per interrompere")
    print()
    print("═" * 60)

    speak("Ciao! Sono Antonio. Come posso aiutarti?")

    conversation_count = 0

    while True:
        try:
            # Ascolta input vocale
            user_input = listen()

            if not user_input:
                continue

            # Comandi di uscita
            if user_input.lower() in ['esci', 'quit', 'exit', 'basta', 'stop']:
                speak("Ciao! A presto!")
                break

            # Invia ad Antonio
            start_time = datetime.now()
            result = ask_antonio(user_input)
            elapsed = (datetime.now() - start_time).total_seconds()

            if result:
                response = result['response']

                # Statistiche
                print(f"\n📊 Stats:")
                print(f"   Latency: {elapsed:.2f}s")
                print(f"   Tokens: {result['tokens_generated']}")
                print(f"   Speed: {result['tokens_per_second']:.1f} t/s")
                print(f"   Confidence: {result['confidence']:.2f}")

                # Leggi risposta
                speak(response)

                conversation_count += 1
            else:
                speak("Mi dispiace, ho avuto un problema. Riprova.")

            print("─" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 Interrotto. Ciao!")
            speak("Ciao!")
            break
        except Exception as e:
            print(f"\n❌ Errore imprevisto: {e}")
            continue

    print(f"\n✓ Conversazioni completate: {conversation_count}")
    print("Grazie per aver usato Antonio Voice Client!")


if __name__ == "__main__":
    main()
