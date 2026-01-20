# JARVIS AI Assistant

A production-grade, modular, voice-controlled AI assistant for Windows.

## Features

- 🎤 **Wake Word Detection**: Say "Jarvis" to activate
- 🗣️ **Natural Speech**: Fast text-to-speech responses
- 🧠 **AI Brain**: Intent classification with fuzzy matching
- 💾 **Persistent Memory**: SQLite-backed memory that survives restarts
- 🔌 **Plugin System**: Easily extensible skill architecture
- 🖥️ **System Control**: Shutdown, restart, volume, screenshots
- 🌐 **Web Integration**: Search, YouTube, website navigation
- 📱 **App Management**: Open and close applications

## Quick Start

### 1. Install Dependencies

```bash
cd jarvis
pip install -r requirements.txt
```

### 2. Run JARVIS

**Voice Mode (Full Experience):**
```bash
python main.py
```

**Text Mode (No Microphone Required):**
```bash
python main.py --text
```

## Project Structure

```
jarvis/
├── main.py                  # Bootloader and entry point
├── core/
│   ├── engine.py            # Main runtime loop
│   ├── brain.py             # Intent classification & AI logic
│   ├── dispatcher.py        # Routes commands to skills
│   └── memory.py            # Persistent SQLite memory
├── audio/
│   ├── tts.py               # Text-to-speech engine
│   └── stt.py               # Speech-to-text engine
├── skills/
│   ├── system.py            # System control (power, volume)
│   ├── apps.py              # Application management
│   ├── time_date.py         # Time and date
│   ├── web.py               # Web search & browsing
│   └── conversation.py      # General conversation
├── config/
│   └── settings.py          # All configuration
├── logs/
│   └── jarvis.log           # Log files
└── requirements.txt         # Dependencies
```

## Voice Commands

### System
- "Jarvis, shutdown/restart/sleep"
- "Jarvis, lock the computer"
- "Jarvis, take a screenshot"

### Volume
- "Jarvis, volume up/down"
- "Jarvis, mute/unmute"
- "Jarvis, set volume to 50"

### Applications (Desktop & Web!)
- "Jarvis, open Chrome/Notepad/Calculator"
- "Jarvis, open YouTube" *(opens in browser)*
- "Jarvis, open Netflix/Gmail/ChatGPT" *(opens in browser)*
- "Jarvis, close Spotify"

### Web
- "Jarvis, search for Python tutorials"
- "Jarvis, play music on YouTube"

### Time & Date
- "Jarvis, what time is it?"
- "Jarvis, what's today's date?"

### Memory
- "Jarvis, remember that my meeting is at 3pm"
- "Jarvis, what do you remember?"

### Conversation
- "Jarvis, tell me a joke"
- "Jarvis, what can you do?"

## 🤖 AI Features (NEW!)

JARVIS now supports intelligent AI-powered conversations using Google Gemini (FREE!).

### Setup AI (Optional but Recommended)

1. Get a FREE API key from: https://makersuite.google.com/app/apikey
2. Set the environment variable:
   ```powershell
   # Windows PowerShell
   $env:GEMINI_API_KEY = "your-api-key-here"
   
   # Or set permanently via System Properties > Environment Variables
   ```
3. Restart JARVIS

Now you can ask JARVIS anything like ChatGPT:
- "Jarvis, explain quantum computing"
- "Jarvis, write me a poem"
- "Jarvis, what's the capital of France?"

## Configuration

Edit `config/settings.py` to customize:

- **Wake words**: Add alternative wake phrases
- **TTS voice**: Change voice, speed, volume
- **App paths**: Add your installed applications
- **User name**: Personalize responses

## Extending JARVIS

### Adding a New Skill

1. Create a new file in `skills/`:

```python
# skills/my_skill.py
from core.dispatcher import skill
from core.brain import IntentCategory, Intent

@skill(
    IntentCategory.CONVERSATION,
    ["my_action"],
    "Description of my skill"
)
def handle_my_action(intent: Intent):
    return {
        "response": "My skill response"
    }
```

2. Import it in `skills/__init__.py`:

```python
from . import my_skill
```

3. Add intent patterns in `core/brain.py`:

```python
"conversation.my_action": [
    "trigger phrase", "another trigger"
]
```

### Adding LLM Integration

The architecture is ready for LLM integration. In `core/brain.py`, you can add:

```python
# In Brain class
def query_llm(self, prompt: str) -> str:
    # Add OpenAI/Anthropic/local LLM integration
    pass
```

## Troubleshooting

### Microphone Issues
- Ensure microphone permissions are granted
- Check default recording device in Windows Sound settings
- Run `python main.py --text` to test without microphone

### PyAudio Installation
If `pip install pyaudio` fails:
```bash
pip install pipwin
pipwin install pyaudio
```

### Speech Recognition Errors
- Ensure internet connection (uses Google Speech API)
- Check microphone sensitivity in settings
- Run in quiet environment

## Requirements

- Windows 10/11
- Python 3.8+
- Working microphone (for voice mode)
- Internet connection (for speech recognition)

## License

MIT License - Use freely for personal and commercial projects.
