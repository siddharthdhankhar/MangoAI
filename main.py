"""
main.py — Entry point for MangoAI.

Run this file to start the assistant:
    python main.py

Voice mode requires a microphone. Text mode works anywhere.
"""

import os
import sys
import speech_recognition as sr
import pyttsx3
from assistant import create_chat, ask


# ── TEXT-TO-SPEECH SETUP ─────────────────────────────────────────────────────

def setup_tts():
    """Initialize text-to-speech engine."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)   # speaking speed (words per minute)
    engine.setProperty("volume", 1.0) # volume (0.0 to 1.0)
    return engine

def speak(engine, text: str):
    """Say text out loud."""
    print(f"Mango: {text}")
    engine.say(text)
    engine.runAndWait()


# ── SPEECH-TO-TEXT ───────────────────────────────────────────────────────────

def listen(recognizer, mic) -> str | None:
    """
    Listen to the microphone and return the transcribed text.
    Returns None if nothing was understood.
    """
    print("Listening...")
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text.lower()
    except sr.WaitTimeoutError:
        return None  # silence — that's fine
    except sr.UnknownValueError:
        return None  # couldn't understand
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
        return None


# ── WAKE WORD ────────────────────────────────────────────────────────────────

WAKE_WORD = "mango"

def wait_for_wake_word(recognizer, mic) -> bool:
    """Keep listening until the wake word is heard. Returns True when detected."""
    print(f'Waiting for wake word "{WAKE_WORD}"...')
    while True:
        text = listen(recognizer, mic)
        if text and WAKE_WORD in text:
            return True


# ── MAIN LOOP ────────────────────────────────────────────────────────────────

def run_voice_mode():
    """Run MangoAI in voice mode (microphone + speaker)."""
    engine     = setup_tts()
    recognizer = sr.Recognizer()
    mic        = sr.Microphone()
    chat       = create_chat()

    speak(engine, "MangoAI is ready. Say 'Mango' to wake me up.")

    while True:
        # Step 1: wait for wake word
        wait_for_wake_word(recognizer, mic)
        speak(engine, "Yes?")

        # Step 2: listen for the actual command
        command = listen(recognizer, mic)
        if not command:
            speak(engine, "I didn't catch that.")
            continue

        if command in ("exit", "quit", "stop", "goodbye"):
            speak(engine, "Goodbye!")
            break

        # Step 3: send command to Gemini, speak the response
        try:
            response = ask(chat, command)
            speak(engine, response)
        except Exception as e:
            speak(engine, "Something went wrong.")
            print(f"Error: {e}")


def run_text_mode():
    """Run MangoAI in text mode (keyboard input, printed output)."""
    chat = create_chat()
    print("MangoAI running in text mode. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        try:
            response = ask(chat, user_input)
            print(f"Mango: {response}\n")
        except Exception as e:
            print(f"Error: {e}\n")


# ── START ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Pass "--text" flag to skip microphone and use keyboard instead
    # Example: python main.py --text
    if "--text" in sys.argv:
        run_text_mode()
    else:
        run_voice_mode()
