"""
api.py — FastAPI server that exposes MangoAI as a REST API.

Run with:
    uvicorn api:app --reload

Then open frontend/index.html in your browser.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from assistant import create_chat, ask

# ── APP SETUP ─────────────────────────────────────────────────────────────────

app = FastAPI(title="MangoAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # open for local dev; tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# One persistent chat session per server run (maintains conversation history)
_chat = create_chat()


# ── SCHEMAS ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    tool_used: Optional[str]
    timestamp: str


class Capability(BaseModel):
    name: str
    description: str
    example: str
    icon: str


# ── TOOL METADATA (for the frontend capability cards) ─────────────────────────

CAPABILITIES: list[Capability] = [
    Capability(name="get_current_time",   description="Tell you the current time",           example="What time is it?",                 icon="🕐"),
    Capability(name="get_current_date",   description="Tell you today's date",               example="What's today's date?",             icon="📅"),
    Capability(name="get_weather",        description="Fetch live weather for any city",      example="What's the weather in Mumbai?",     icon="🌤"),
    Capability(name="get_latest_news",    description="Top 3 BBC world news headlines",       example="What's in the news?",              icon="📰"),
    Capability(name="search_wikipedia",   description="2-sentence Wikipedia summary",         example="Search Wikipedia for black holes",  icon="📚"),
    Capability(name="play_music",         description="Search YouTube for a song",            example="Play Blinding Lights",             icon="🎵"),
    Capability(name="set_timer",          description="Countdown timer with beep alert",      example="Set a timer for 10 minutes",        icon="⏱"),
    Capability(name="open_website",       description="Open a website in the browser",        example="Open YouTube",                     icon="🌐"),
    Capability(name="open_app",           description="Launch any installed application",     example="Open Spotify",                     icon="🚀"),
    Capability(name="close_app",          description="Close a running application",          example="Close Notepad",                    icon="✖"),
    Capability(name="change_volume",      description="Raise or lower system volume",         example="Volume up",                        icon="🔊"),
    Capability(name="mute_volume",        description="Toggle system mute",                   example="Mute",                             icon="🔇"),
    Capability(name="control_media",      description="Play, pause, skip tracks",             example="Next track",                       icon="⏭"),
    Capability(name="remember_fact",      description="Save a fact to persistent memory",     example="Remember that my city is Pune",    icon="🧠"),
    Capability(name="recall_fact",        description="Recall a previously saved fact",       example="What's my city?",                  icon="💭"),
    Capability(name="manage_todo",        description="Add, read, or clear a to-do list",     example="Add milk to my list",              icon="✅"),
    Capability(name="find_file",          description="Find & open a file on your computer",  example="Find my resume",                   icon="🔍"),
    Capability(name="sleep_computer",     description="Put the computer to sleep",            example="Sleep the computer",               icon="💤"),
]

# Map tool function names → metadata for quick lookup
_tool_map = {c.name: c for c in CAPABILITIES}


def _extract_tool(response_obj) -> Optional[str]:
    """
    Walk the Gemini response parts to find any function call that was made.
    Returns the tool name string, or None.
    """
    try:
        for candidate in response_obj.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    return part.function_call.name
    except Exception:
        pass
    return None


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "MangoAI API is running 🥭"}


@app.get("/capabilities", response_model=list[Capability])
def get_capabilities():
    """Return all available tools with metadata for the frontend."""
    return CAPABILITIES


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a message to MangoAI and get a response."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    try:
        # We need the raw response object to inspect tool calls,
        # so we call the SDK directly here instead of ask()
        raw = _chat.send_message(req.message)
        response_text = raw.text or ""

        # Try to pull the tool name from intermediate history
        tool_used: Optional[str] = None
        try:
            history = _chat.get_history()
            # Walk history backwards to find the most recent function call
            for turn in reversed(history):
                for part in turn.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        tool_used = part.function_call.name
                        raise StopIteration
        except StopIteration:
            pass

        return ChatResponse(
            response=response_text,
            tool_used=tool_used,
            timestamp=datetime.now().strftime("%I:%M %p"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
def reset_chat():
    """Start a fresh conversation (clears history)."""
    global _chat
    _chat = create_chat()
    return {"status": "ok", "message": "Conversation reset."}
