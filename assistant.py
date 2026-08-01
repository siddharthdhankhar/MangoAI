"""
assistant.py — The brain of MangoAI.

This file handles all communication with the Gemini AI.
It gives Gemini the list of tools and manages the conversation history.

How function calling works:
  1. You send a message to Gemini.
  2. Gemini decides if it needs to call a tool (e.g., get_weather("London")).
  3. The SDK automatically calls that function and sends the result back.
  4. Gemini uses the result to give you a final answer.

That's it. No magic.
"""

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = (
    "You are Mango, a friendly voice assistant. "
    "Keep every response short (1–2 sentences), natural, and spoken-word friendly. "
    "Use your tools whenever a user asks for something you can action."
)


def create_chat():
    """Create and return a Gemini chat session with all tools attached."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Add it to your .env file.")

    client = genai.Client(api_key=api_key)

    # Gemini reads our Python functions directly.
    # It uses the function name, type hints, and docstring to know when to call each one.
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            tools=ALL_TOOLS,
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
        ),
    )
    return chat


def ask(chat, user_input: str) -> str:
    """Send a message to Gemini and return its text response."""
    response = chat.send_message(user_input)
    return response.text
