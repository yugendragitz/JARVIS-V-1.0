"""
JARVIS AI Brain
Intent classification, decision making, and response generation
"""

import re
import random
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logger.warning("rapidfuzz not available, using basic matching")


class IntentCategory(Enum):
    """High-level intent categories"""
    SYSTEM = auto()
    APPLICATION = auto()
    WEB = auto()
    TIME_DATE = auto()
    CONVERSATION = auto()
    MEMORY = auto()
    VOLUME = auto()
    UNKNOWN = auto()


@dataclass
class Intent:
    """Represents a classified intent"""
    category: IntentCategory
    action: str
    confidence: float
    entities: Dict[str, Any]
    raw_text: str


class Brain:
    """
    JARVIS AI Brain
    
    Handles:
    - Intent classification
    - Entity extraction
    - Response generation
    - Context awareness
    """
    
    def __init__(self, confidence_threshold: int = 65):
        self._confidence_threshold = confidence_threshold
        self._intent_patterns = self._build_intent_patterns()
        self._context: Dict[str, Any] = {}
        
    def _build_intent_patterns(self) -> Dict[str, List[str]]:
        """Build intent pattern database"""
        return {
            # System commands
            "system.shutdown": [
                "shutdown", "shut down", "power off", "turn off computer",
                "shutdown computer", "shut down the computer"
            ],
            "system.restart": [
                "restart", "reboot", "restart computer", "reboot computer",
                "restart the computer"
            ],
            "system.lock": [
                "lock", "lock computer", "lock screen", "lock the computer"
            ],
            "system.screenshot": [
                "screenshot", "take screenshot", "capture screen", "screen capture",
                "take a screenshot"
            ],
            
            # Volume commands
            "volume.up": [
                "volume up", "increase volume", "louder", "turn up volume",
                "raise volume", "turn it up"
            ],
            "volume.down": [
                "volume down", "decrease volume", "quieter", "turn down volume",
                "lower volume", "turn it down"
            ],
            "volume.mute": [
                "mute", "mute volume", "silence", "mute audio", "mute sound"
            ],
            "volume.unmute": [
                "unmute", "unmute volume", "unmute audio"
            ],
            "volume.set": [
                "set volume to", "volume to", "set volume"
            ],
            
            # Application commands
            "app.open": [
                "open", "launch", "start", "run", "execute", "fire up"
            ],
            "app.close": [
                "close", "quit", "exit", "kill", "terminate", "end"
            ],
            
            # Web commands
            "web.search": [
                "search", "google", "look up", "find", "search for",
                "search the web for", "google search"
            ],
            "web.open": [
                "open website", "go to", "visit", "open site", "browse to",
                "navigate to"
            ],
            "web.youtube": [
                "play on youtube", "youtube", "search youtube", "play video",
                "watch"
            ],
            
            # Time/Date - IMPORTANT: action names must match skill registrations
            "time_date.time": [
                "what time", "current time", "tell me the time", "what's the time",
                "time please", "what is the time", "time", "the time", "whats the time",
                "tell time", "show time", "give me the time", "what time is it"
            ],
            "time_date.date": [
                "what date", "current date", "today's date", "what's the date",
                "what day is it", "what is today", "what's today's date",
                "whats today", "today date", "date today", "date", "the date",
                "tell me the date", "what day", "today"
            ],
            
            # Memory commands
            "memory.remember": [
                "remember", "remember that", "store", "save", "note that",
                "keep in mind"
            ],
            "memory.recall": [
                "recall", "what do you remember", "what did i tell you",
                "do you remember", "what do you know about"
            ],
            "memory.forget": [
                "forget", "forget that", "delete", "remove from memory"
            ],
            
            # Conversation
            "conversation.greeting": [
                "hello", "hi", "hey", "good morning", "good afternoon",
                "good evening", "howdy", "what's up"
            ],
            "conversation.farewell": [
                "goodbye", "bye", "see you", "farewell", "good night",
                "i'm leaving", "that's all"
            ],
            "conversation.thanks": [
                "thank you", "thanks", "appreciate it", "cheers"
            ],
            "conversation.how_are_you": [
                "how are you", "how do you feel", "how's it going",
                "what's up", "how are things"
            ],
            "conversation.who_are_you": [
                "who are you", "what are you", "what's your name",
                "tell me about yourself", "introduce yourself"
            ],
            "conversation.capabilities": [
                "what can you do", "help", "what are your capabilities",
                "what do you do", "show me what you can do"
            ],
            "conversation.joke": [
                "tell me a joke", "joke", "make me laugh", "say something funny"
            ],
            "conversation.stop": [
                "stop", "cancel", "nevermind", "never mind", "abort",
                "shut up", "be quiet", "stop talking"
            ],
        }
    
    def classify_intent(self, text: str) -> Intent:
        """
        Classify the intent of user input
        
        Args:
            text: User's spoken/typed input
            
        Returns:
            Intent object with classification details
        """
        text_lower = text.lower().strip()
        
        if not text_lower:
            return Intent(
                category=IntentCategory.UNKNOWN,
                action="unknown",
                confidence=0.0,
                entities={},
                raw_text=text
            )
        
        # CRITICAL: Protect common greetings from being misclassified
        greeting_words = ["hi", "hello", "hey", "howdy"]
        if text_lower in greeting_words or (len(text_lower.split()) == 1 and text_lower in greeting_words):
            return Intent(
                category=IntentCategory.CONVERSATION,
                action="greeting",
                confidence=100.0,
                entities={},
                raw_text=text
            )
        
        best_match = None
        best_score = 0
        
        for intent_key, patterns in self._intent_patterns.items():
            score = self._match_patterns(text_lower, patterns)
            
            if score > best_score:
                best_score = score
                best_match = intent_key
        
        # Determine category and action from intent key
        if best_match and best_score >= self._confidence_threshold:
            category_str, action = best_match.split(".", 1)
            category = self._get_category(category_str)
            entities = self._extract_entities(text_lower, best_match)
            
            return Intent(
                category=category,
                action=action,
                confidence=best_score,
                entities=entities,
                raw_text=text
            )
        
        # Check for app open pattern specifically
        app_match = self._check_app_open(text_lower)
        if app_match:
            return Intent(
                category=IntentCategory.APPLICATION,
                action="open",
                confidence=85.0,
                entities={"app_name": app_match},
                raw_text=text
            )
        
        # Default to conversation/unknown
        return Intent(
            category=IntentCategory.CONVERSATION,
            action="general",
            confidence=50.0,
            entities={},
            raw_text=text
        )
    
    def _match_patterns(self, text: str, patterns: List[str]) -> float:
        """Match text against patterns, return best score"""
        text = text.lower().strip()
        text_words = text.split()
        
        # For very short inputs (1-2 words), be strict with matching
        is_short_input = len(text_words) <= 2 and len(text) <= 10
        
        # First check for exact word matches (highest priority)
        for pattern in patterns:
            pattern_lower = pattern.lower()
            pattern_words = pattern_lower.split()
            
            # Exact match of entire pattern
            if pattern_lower == text:
                return 100.0
            
            # Exact word match (any word in text matches any word in pattern)
            for text_word in text_words:
                if text_word in pattern_words:
                    # For short inputs, require exact word match
                    if is_short_input and text_word == text:
                        return 95.0
                    elif not is_short_input:
                        return 90.0
            
            # Check if all pattern words are in text (for longer patterns)
            if len(pattern_words) > 1 and all(word in text_words for word in pattern_words):
                return 95.0
        
        # Skip fuzzy matching for very short inputs to avoid false matches
        if is_short_input:
            return 0.0
        
        # Then use fuzzy matching for longer inputs only
        if FUZZY_AVAILABLE:
            result = process.extractOne(text, patterns, scorer=fuzz.partial_ratio)
            if result:
                # Reduce fuzzy match scores to give priority to exact matches
                return min(result[1] * 0.7, 70.0)
        else:
            # Basic substring matching
            for pattern in patterns:
                if pattern in text:
                    return 65.0
        
        return 0.0
    
    def _get_category(self, category_str: str) -> IntentCategory:
        """Convert string to IntentCategory"""
        mapping = {
            "system": IntentCategory.SYSTEM,
            "app": IntentCategory.APPLICATION,
            "web": IntentCategory.WEB,
            "time": IntentCategory.TIME_DATE,
            "date": IntentCategory.TIME_DATE,
            "time_date": IntentCategory.TIME_DATE,
            "conversation": IntentCategory.CONVERSATION,
            "memory": IntentCategory.MEMORY,
            "volume": IntentCategory.VOLUME,
        }
        return mapping.get(category_str, IntentCategory.UNKNOWN)
    
    def _extract_entities(self, text: str, intent_key: str) -> Dict[str, Any]:
        """Extract entities from text based on intent"""
        entities = {}
        
        if intent_key == "app.open":
            # Extract app name
            for trigger in ["open", "launch", "start", "run"]:
                if trigger in text:
                    parts = text.split(trigger, 1)
                    if len(parts) > 1:
                        app_name = parts[1].strip()
                        # Clean common suffixes
                        app_name = re.sub(r'\s+(please|now|for me)$', '', app_name)
                        entities["app_name"] = app_name
                        break
        
        elif intent_key == "app.close":
            for trigger in ["close", "quit", "exit", "kill"]:
                if trigger in text:
                    parts = text.split(trigger, 1)
                    if len(parts) > 1:
                        entities["app_name"] = parts[1].strip()
                        break
        
        elif intent_key.startswith("web.search"):
            for trigger in ["search for", "search", "google", "look up", "find"]:
                if trigger in text:
                    parts = text.split(trigger, 1)
                    if len(parts) > 1:
                        entities["query"] = parts[1].strip()
                        break
        
        elif intent_key == "web.youtube":
            for trigger in ["play", "youtube", "watch"]:
                if trigger in text:
                    parts = text.split(trigger, 1)
                    if len(parts) > 1:
                        query = parts[1].strip()
                        query = re.sub(r'^(on youtube|video)\s*', '', query)
                        entities["query"] = query
                        break
        
        elif intent_key == "volume.set":
            # Extract volume level
            numbers = re.findall(r'\d+', text)
            if numbers:
                entities["level"] = int(numbers[0])
        
        elif intent_key == "memory.remember":
            for trigger in ["remember that", "remember", "note that"]:
                if trigger in text:
                    parts = text.split(trigger, 1)
                    if len(parts) > 1:
                        entities["content"] = parts[1].strip()
                        break
        
        elif intent_key == "memory.recall":
            for trigger in ["about", "remember"]:
                if trigger in text:
                    parts = text.split(trigger, 1)
                    if len(parts) > 1:
                        entities["query"] = parts[1].strip()
                        break
        
        return entities
    
    def _check_app_open(self, text: str) -> Optional[str]:
        """Check if text is requesting to open an app"""
        # Web-based apps that should open in browser, not as .exe
        web_apps = [
            "youtube", "netflix", "spotify web", "facebook", "instagram",
            "twitter", "whatsapp", "telegram", "gmail", "google drive",
            "github", "linkedin", "reddit", "amazon", "flipkart",
            "chatgpt", "google", "wikipedia", "stackoverflow"
        ]
        
        for web_app in web_apps:
            if web_app in text:
                # These should be handled by web skills, not app skills
                return None
        
        # Common desktop app names
        apps = [
            "chrome", "firefox", "edge", "browser",
            "notepad", "calculator", "word", "excel", "powerpoint",
            "spotify", "discord", "vscode", "code",
            "file explorer", "explorer", "command prompt", "cmd",
            "powershell", "terminal", "task manager", "settings",
            "control panel", "paint", "photos", "camera", "teams",
            "zoom", "vlc", "media player", "snipping tool"
        ]
        
        for app in apps:
            if app in text:
                # Check if it's in an "open" context
                open_triggers = ["open", "launch", "start", "run"]
                if any(trigger in text for trigger in open_triggers):
                    return app
        
        return None
    
    def generate_response(self, intent: Intent, result: Any = None) -> str:
        """Generate a Jarvis-style response based on intent and result"""
        from config import RESPONSES, USER_NAME
        
        # Replace placeholder
        def personalize(text: str) -> str:
            return text.replace("{user}", USER_NAME)
        
        # Acknowledgment responses
        if intent.action in ["shutdown", "restart", "sleep", "lock"]:
            return personalize(random.choice(RESPONSES["acknowledgment"]))
        
        # Error responses
        if result and isinstance(result, dict) and result.get("error"):
            return personalize(random.choice(RESPONSES["error"]))
        
        # Specific responses
        if intent.action == "greeting":
            return personalize(random.choice(RESPONSES["greeting"]))
        
        if intent.action == "farewell":
            return personalize(random.choice(RESPONSES["farewell"]))
        
        if intent.action == "thanks":
            responses = [
                f"You're welcome, {USER_NAME}.",
                "Happy to help.",
                f"Of course, {USER_NAME}.",
                "Anytime.",
            ]
            return random.choice(responses)
        
        if intent.action == "how_are_you":
            responses = [
                f"I'm functioning optimally, {USER_NAME}. Thank you for asking.",
                f"All systems operational, {USER_NAME}.",
                f"I'm doing well, {USER_NAME}. Ready to assist.",
            ]
            return random.choice(responses)
        
        if intent.action == "who_are_you":
            return (f"I am Jarvis, your personal AI assistant. "
                   f"I'm here to help you with various tasks, {USER_NAME}.")
        
        if intent.action == "capabilities":
            return (f"I can help you with many things, {USER_NAME}. "
                   "I can open applications, control system settings, "
                   "search the web, tell you the time and date, "
                   "remember things for you, and have conversations. "
                   "Just say my name followed by your request.")
        
        if intent.action == "joke":
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs.",
                "I told my computer I needed a break. Now it won't stop sending me vacation ads.",
                "Why did the developer go broke? Because he used up all his cache.",
                "I would tell you a UDP joke, but you might not get it.",
            ]
            return random.choice(jokes)
        
        if intent.action == "stop":
            return f"Of course, {USER_NAME}."
        
        # Default acknowledgment
        return personalize(random.choice(RESPONSES["acknowledgment"]))
    
    def set_context(self, key: str, value: Any):
        """Set context for conversation continuity"""
        self._context[key] = value
    
    def get_context(self, key: str) -> Any:
        """Get context value"""
        return self._context.get(key)
    
    def clear_context(self):
        """Clear conversation context"""
        self._context.clear()


# Global brain instance
_brain_instance: Optional[Brain] = None


def get_brain() -> Brain:
    """Get or create global brain instance"""
    global _brain_instance
    if _brain_instance is None:
        from config import INTENT_CONFIDENCE_THRESHOLD
        _brain_instance = Brain(confidence_threshold=INTENT_CONFIDENCE_THRESHOLD)
    return _brain_instance
