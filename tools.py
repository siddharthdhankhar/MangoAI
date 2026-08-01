"""
tools.py — All the things MangoAI can do.

Each function here is a "tool" that the Gemini AI can call.
The AI reads the function name, arguments, and docstring to decide when to use it.
"""

import os
import time
import json
import datetime
import threading
import webbrowser
import urllib.parse

import requests
import feedparser
import pyautogui
import wikipedia
from AppOpener import open as app_open, close as app_close


# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
TODO_FILE   = os.path.join(BASE_DIR, "todo.txt")


# ── DATE & TIME ──────────────────────────────────────────────────────────────

def get_current_time() -> str:
    """Return the current time."""
    return datetime.datetime.now().strftime("%I:%M %p")

def get_current_date() -> str:
    """Return today's date."""
    return datetime.datetime.now().strftime("%A, %B %d %Y")


# ── VOLUME & MEDIA ───────────────────────────────────────────────────────────

def mute_volume() -> str:
    """Mute or unmute the system volume."""
    pyautogui.press("volumemute")
    return "Done."

def change_volume(direction: str) -> str:
    """
    Raise or lower the volume.
    direction: "up" to increase, "down" to decrease.
    """
    key = "volumeup" if direction == "up" else "volumedown"
    for _ in range(5):
        pyautogui.press(key)
    return f"Volume {direction}."

def control_media(action: str) -> str:
    """
    Control music/video playback.
    action: "next", "previous", or "playpause".
    """
    mapping = {
        "next":      "nexttrack",
        "previous":  "prevtrack",
        "playpause": "playpause",
    }
    pyautogui.press(mapping.get(action, "playpause"))
    return f"Media: {action}."


# ── APPS & WEBSITES ──────────────────────────────────────────────────────────

def open_website(website_name: str) -> str:
    """
    Open a website in the browser.
    website_name: e.g. "google", "youtube", "gmail", "maps".
    """
    shortcuts = {
        "google":  "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "gmail":   "https://mail.google.com",
        "maps":    "https://maps.google.com",
    }
    url = shortcuts.get(website_name.lower())
    if url:
        webbrowser.open(url)
        return f"Opening {website_name}."
    # fallback: Google search
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(website_name)}")
    return f"Searching for {website_name}."

def open_app(app_name: str) -> str:
    """Open an installed application by name."""
    try:
        app_open(app_name, match_closest=True)
        return f"Opening {app_name}."
    except Exception:
        return f"Could not find '{app_name}'."

def close_app(app_name: str) -> str:
    """Close a running application by name."""
    try:
        app_close(app_name, match_closest=True)
        return f"Closing {app_name}."
    except Exception:
        return f"Could not close '{app_name}'."

def sleep_computer() -> str:
    """Put the computer to sleep."""
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "Sleeping."


# ── SEARCH & INFORMATION ─────────────────────────────────────────────────────

def search_wikipedia(topic: str) -> str:
    """Search Wikipedia and return a 2-sentence summary."""
    try:
        return wikipedia.summary(topic, sentences=2)
    except Exception as e:
        return f"Wikipedia error: {e}"

def get_weather(location: str) -> str:
    """Get the current weather for a city."""
    try:
        res = requests.get(f"https://wttr.in/{location}?format=%l:+%C,+%t", timeout=5)
        if res.status_code == 200:
            return res.text.strip()
    except Exception:
        pass
    return "Could not fetch weather."

def get_latest_news() -> str:
    """Get the top 3 world news headlines from BBC."""
    try:
        feed = feedparser.parse("http://feeds.bbci.co.uk/news/world/rss.xml")
        headlines = [entry.title for entry in feed.entries[:3]]
        return " | ".join(headlines)
    except Exception:
        return "Could not fetch news."

def play_music(song: str) -> str:
    """Search for a song on YouTube and open it."""
    query = urllib.parse.urlencode({"search_query": song})
    webbrowser.open(f"https://www.youtube.com/results?{query}")
    return f"Searching YouTube for '{song}'."

def find_file(filename: str) -> str:
    """Find a file by name and open it (searches Desktop, Documents, Downloads)."""
    home = os.path.expanduser("~")
    for folder in ["Desktop", "Documents", "Downloads"]:
        for root, _, files in os.walk(os.path.join(home, folder)):
            for f in files:
                if filename.lower() in f.lower():
                    os.startfile(os.path.join(root, f))
                    return f"Opened '{f}'."
    return f"Could not find '{filename}'."


# ── TIMER ────────────────────────────────────────────────────────────────────

def set_timer(minutes: int) -> str:
    """Set a countdown timer. When it ends, it beeps."""
    if minutes <= 0:
        return "Please give a positive number of minutes."

    def _countdown():
        time.sleep(minutes * 60)
        for _ in range(5):
            print("\a", end="", flush=True)  # terminal beep

    threading.Thread(target=_countdown, daemon=True).start()
    return f"Timer set for {minutes} minute{'s' if minutes != 1 else ''}."


# ── MEMORY ───────────────────────────────────────────────────────────────────

def remember_fact(subject: str, value: str) -> str:
    """
    Save a fact to memory so it can be recalled later.
    Example: subject="favorite color", value="blue"
    """
    memory = _load_memory()
    memory[subject] = value
    _save_memory(memory)
    return f"Got it. I'll remember that your {subject} is {value}."

def recall_fact(subject: str) -> str:
    """Recall a previously saved fact."""
    memory = _load_memory()
    if subject in memory:
        return f"Your {subject} is {memory[subject]}."
    return f"I don't have anything saved about '{subject}'."

def _load_memory() -> dict:
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_memory(data: dict) -> None:
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── TO-DO LIST ───────────────────────────────────────────────────────────────

def manage_todo(action: str, item: str = "") -> str:
    """
    Manage a simple to-do list.
    action: "add" (requires item), "read", or "clear".
    """
    if action == "add":
        if not item:
            return "What should I add to the list?"
        with open(TODO_FILE, "a") as f:
            f.write(f"- {item}\n")
        return f"Added '{item}' to your list."

    elif action == "read":
        if not os.path.exists(TODO_FILE):
            return "Your list is empty."
        content = open(TODO_FILE).read().strip()
        return content if content else "Your list is empty."

    elif action == "clear":
        if os.path.exists(TODO_FILE):
            os.remove(TODO_FILE)
        return "List cleared."

    return "I didn't understand that. Try 'add', 'read', or 'clear'."


# ── TOOL REGISTRY ────────────────────────────────────────────────────────────
# This is the list we hand to Gemini. It reads the function signatures
# and docstrings to understand what each tool does and when to call it.

ALL_TOOLS = [
    get_current_time,
    get_current_date,
    mute_volume,
    change_volume,
    control_media,
    open_website,
    open_app,
    close_app,
    sleep_computer,
    search_wikipedia,
    get_weather,
    get_latest_news,
    play_music,
    find_file,
    set_timer,
    remember_fact,
    recall_fact,
    manage_todo,
]
