# MangoAI 🥭

A personal voice assistant powered by Google's Gemini AI.  
Speak a command, and MangoAI figures out what to do — no rigid keyword matching, just natural conversation.

## How it works

MangoAI uses **Gemini's function calling** feature. Instead of a big chain of `if/elif` checks, the AI reads the available tools (Python functions) and decides on its own which one to call based on what you say.

```
You say:  "What's the weather in Mumbai?"
   ↓
Gemini sees the get_weather(location) tool
   ↓
Gemini calls get_weather("Mumbai")
   ↓
MangoAI speaks the result back to you
```

## Project structure

```
MangoAI/
├── main.py        # Entry point — starts voice or text mode
├── assistant.py   # Gemini AI setup and conversation logic  
├── tools.py       # All commands the AI can use
├── .env           # Your API key (never committed to Git)
└── requirements.txt
```

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/siddharthdhankhar/MangoAI.git
cd MangoAI
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your Gemini API key**

Copy the example env file and fill in your key:
```bash
copy .env.example .env
```
Then open `.env` and replace `your_gemini_api_key_here` with your real key.  
Get a free key at [aistudio.google.com](https://aistudio.google.com)

## Running

**Voice mode** (requires a microphone):
```bash
python main.py
```
Say **"Mango"** to wake it up, then give your command.

**Text mode** (no microphone needed):
```bash
python main.py --text
```

## What it can do

| Capability | Example command |
|---|---|
| Current time & date | "What time is it?" |
| Weather | "What's the weather in Delhi?" |
| Open apps | "Open Spotify" |
| Open websites | "Open YouTube" |
| Play music | "Play Blinding Lights" |
| Wikipedia search | "Search Wikipedia for black holes" |
| Latest news | "What's in the news?" |
| Set a timer | "Set a timer for 10 minutes" |
| Volume control | "Volume up" / "Mute" |
| Media control | "Next track" / "Pause" |
| To-do list | "Add milk to my list" |
| Memory | "Remember that my name is Alex" |

## Tech stack

- **Python 3.10+**
- **Google Gemini API** (`google-genai`) — AI model and function calling
- **SpeechRecognition** — captures microphone input
- **pyttsx3** — offline text-to-speech
- **requests / feedparser** — weather and news APIs
