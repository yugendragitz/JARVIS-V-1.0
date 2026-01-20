"""
JARVIS Configuration Module
Central configuration for all system parameters
"""

import os
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# PATH CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
MEMORY_DB = DATA_DIR / "memory.db"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# JARVIS IDENTITY
# ══════════════════════════════════════════════════════════════════════════════

ASSISTANT_NAME = "Jarvis"
WAKE_WORDS = ["jarvis", "hey jarvis", "ok jarvis", "yo jarvis"]
USER_NAME = "Sir"  # Can be personalized

# ══════════════════════════════════════════════════════════════════════════════
# AUDIO CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Speech Recognition
SR_ENERGY_THRESHOLD = 4000
SR_PAUSE_THRESHOLD = 0.8
SR_PHRASE_TIME_LIMIT = 10
SR_TIMEOUT = 5
SR_LANGUAGE = "en-US"

# Text-to-Speech
TTS_RATE = 175  # Words per minute
TTS_VOLUME = 1.0  # 0.0 to 1.0
TTS_VOICE_INDEX = 0  # 0 = default, change based on available voices

# ══════════════════════════════════════════════════════════════════════════════
# BRAIN CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Intent matching threshold (0-100, higher = stricter)
INTENT_CONFIDENCE_THRESHOLD = 65

# Conversation mode timeout (seconds)
CONVERSATION_TIMEOUT = 30

# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

# App paths (customize for your system)
APP_PATHS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "vscode": r"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "spotify": r"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe",
    "discord": r"C:\Users\{username}\AppData\Local\Discord\Update.exe --processStart Discord.exe",
    "file explorer": "explorer.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
}

# Replace {username} with actual username
import getpass
_username = getpass.getuser()
APP_PATHS = {k: v.replace("{username}", _username) for k, v in APP_PATHS.items()}

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

LOG_FILE = LOGS_DIR / "jarvis.log"
LOG_LEVEL = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# ══════════════════════════════════════════════════════════════════════════════
# FEATURE FLAGS
# ══════════════════════════════════════════════════════════════════════════════

ENABLE_WAKE_WORD = True
ENABLE_CONTINUOUS_LISTENING = True
ENABLE_MEMORY = True
ENABLE_LOGGING = True
DEBUG_MODE = False

# ══════════════════════════════════════════════════════════════════════════════
# AI CONFIGURATION (Google Gemini)
# ══════════════════════════════════════════════════════════════════════════════

# Get your FREE API key from: https://makersuite.google.com/app/apikey
# Then set it here or as environment variable GEMINI_API_KEY
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# AI Model settings
AI_MODEL = "gemini-1.5-flash"  # Fast and free
AI_MAX_TOKENS = 500  # Keep responses concise
AI_TEMPERATURE = 0.7  # Balance creativity and accuracy

# ══════════════════════════════════════════════════════════════════════════════
# RESPONSES (Jarvis personality)
# ══════════════════════════════════════════════════════════════════════════════

RESPONSES = {
    "greeting": [
        "At your service, {user}.",
        "Yes, {user}?",
        "How may I assist you, {user}?",
        "Online and ready, {user}.",
        "I'm here, {user}.",
    ],
    "acknowledgment": [
        "Right away, {user}.",
        "On it, {user}.",
        "Consider it done.",
        "Executing now.",
        "As you wish, {user}.",
    ],
    "farewell": [
        "Goodbye, {user}. I'll be here if you need me.",
        "Shutting down. Until next time, {user}.",
        "Going offline. Stay safe, {user}.",
    ],
    "error": [
        "I apologize, {user}. I encountered an issue.",
        "Something went wrong, {user}. Let me try again.",
        "I'm having trouble with that, {user}.",
    ],
    "not_understood": [
        "I didn't quite catch that, {user}.",
        "Could you repeat that, {user}?",
        "I'm not sure I understand, {user}.",
    ],
    "thinking": [
        "Processing...",
        "One moment...",
        "Let me think about that...",
    ],
}
