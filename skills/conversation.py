"""
JARVIS Conversation Skills
General conversation, memory operations, fallback responses
"""

import random
import logging
from typing import Dict, Any
from datetime import datetime

from core.dispatcher import skill, get_dispatcher
from core.brain import IntentCategory, Intent
from core.memory import get_memory
from config import USER_NAME, ASSISTANT_NAME

logger = logging.getLogger(__name__)


@skill(
    IntentCategory.CONVERSATION,
    ["greeting"],
    "Handle greetings"
)
def handle_greeting(intent: Intent) -> Dict[str, Any]:
    """Respond to greetings"""
    hour = datetime.now().hour
    
    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    responses = [
        f"{time_greeting}, {USER_NAME}. How may I assist you?",
        f"Hello, {USER_NAME}. What can I do for you?",
        f"{time_greeting}, {USER_NAME}. I'm at your service.",
        f"Greetings, {USER_NAME}. How can I help?",
    ]
    
    return {"response": random.choice(responses)}


@skill(
    IntentCategory.CONVERSATION,
    ["farewell"],
    "Handle farewells"
)
def handle_farewell(intent: Intent) -> Dict[str, Any]:
    """Respond to farewells"""
    hour = datetime.now().hour
    
    if hour >= 22 or hour < 5:
        responses = [
            f"Good night, {USER_NAME}. Rest well.",
            f"Sleep well, {USER_NAME}. I'll be here when you need me.",
        ]
    else:
        responses = [
            f"Goodbye, {USER_NAME}. I'll be here if you need me.",
            f"Until next time, {USER_NAME}.",
            f"Take care, {USER_NAME}.",
        ]
    
    return {"response": random.choice(responses)}


@skill(
    IntentCategory.CONVERSATION,
    ["thanks"],
    "Handle thanks"
)
def handle_thanks(intent: Intent) -> Dict[str, Any]:
    """Respond to thanks"""
    responses = [
        f"You're welcome, {USER_NAME}.",
        "Happy to help.",
        f"Of course, {USER_NAME}.",
        "Anytime.",
        "My pleasure.",
    ]
    return {"response": random.choice(responses)}


@skill(
    IntentCategory.CONVERSATION,
    ["how_are_you"],
    "Handle 'how are you'"
)
def handle_how_are_you(intent: Intent) -> Dict[str, Any]:
    """Respond to 'how are you'"""
    responses = [
        f"I'm functioning optimally, {USER_NAME}. Thank you for asking. How can I assist you?",
        f"All systems operational, {USER_NAME}. What can I do for you?",
        f"I'm doing well, {USER_NAME}. Ready to help with whatever you need.",
        f"Running at peak efficiency, {USER_NAME}. What's on your mind?",
    ]
    return {"response": random.choice(responses)}


@skill(
    IntentCategory.CONVERSATION,
    ["who_are_you"],
    "Handle identity questions"
)
def handle_who_are_you(intent: Intent) -> Dict[str, Any]:
    """Respond to identity questions"""
    return {
        "response": (
            f"I am {ASSISTANT_NAME}, your personal AI assistant. "
            f"I'm designed to help you with various tasks including "
            "opening applications, searching the web, controlling system settings, "
            "managing your schedule, and much more. "
            f"Think of me as your digital companion, {USER_NAME}."
        )
    }


@skill(
    IntentCategory.CONVERSATION,
    ["capabilities", "help"],
    "List capabilities"
)
def handle_capabilities(intent: Intent) -> Dict[str, Any]:
    """List what Jarvis can do"""
    capabilities = [
        "Open and close applications",
        "Search the web and YouTube",
        "Tell you the time and date",
        "Control system volume",
        "Take screenshots",
        "Shutdown, restart, or lock your computer",
        "Remember information for you",
        "Have conversations",
    ]
    
    response = (
        f"Here's what I can help you with, {USER_NAME}:\n"
        + "\n".join(f"• {cap}" for cap in capabilities)
        + "\n\nJust say my name followed by your request."
    )
    
    # For speech, provide a shorter version
    speech_response = (
        f"I can help you with many things, {USER_NAME}. "
        "I can open applications, search the web, control your computer, "
        "tell you the time, remember things, and more. "
        "What would you like me to do?"
    )
    
    return {"response": speech_response, "detailed": response}


@skill(
    IntentCategory.CONVERSATION,
    ["joke"],
    "Tell a joke"
)
def handle_joke(intent: Intent) -> Dict[str, Any]:
    """Tell a joke"""
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "I told my computer I needed a break. Now it won't stop sending me vacation ads.",
        "Why did the developer go broke? Because he used up all his cache.",
        "I would tell you a UDP joke, but you might not get it.",
        "Why do Java developers wear glasses? Because they can't C#.",
        "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
        "There are only 10 types of people in the world: those who understand binary and those who don't.",
        "Why did the programmer quit his job? Because he didn't get arrays.",
        "What's a programmer's favorite hangout place? Foo Bar.",
        "Why do programmers always mix up Halloween and Christmas? Because Oct 31 equals Dec 25.",
    ]
    return {"response": random.choice(jokes)}


@skill(
    IntentCategory.CONVERSATION,
    ["stop", "cancel"],
    "Stop/cancel current action"
)
def handle_stop(intent: Intent) -> Dict[str, Any]:
    """Handle stop/cancel commands"""
    responses = [
        f"Alright, {USER_NAME}.",
        "Okay, stopping.",
        "Cancelled.",
        f"Of course, {USER_NAME}.",
    ]
    return {"response": random.choice(responses)}


# ══════════════════════════════════════════════════════════════════════════════
# MEMORY OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

@skill(
    IntentCategory.MEMORY,
    ["remember"],
    "Remember information"
)
def handle_remember(intent: Intent) -> Dict[str, Any]:
    """Store information in memory"""
    content = intent.entities.get("content", "").strip()
    
    if not content:
        raw = intent.raw_text.lower()
        for trigger in ["remember that", "remember", "note that", "save"]:
            if trigger in raw:
                content = raw.split(trigger, 1)[-1].strip()
                break
    
    if not content:
        return {
            "response": f"What would you like me to remember, {USER_NAME}?",
            "error": "no_content"
        }
    
    memory = get_memory()
    
    # Try to categorize the memory
    category = "general"
    if any(word in content.lower() for word in ["name is", "called", "i am"]):
        category = "personal"
    elif any(word in content.lower() for word in ["like", "love", "favorite", "prefer"]):
        category = "preferences"
    elif any(word in content.lower() for word in ["meeting", "appointment", "deadline", "tomorrow"]):
        category = "schedule"
    
    memory.learn_fact(category, content, source="user_told")
    
    logger.info(f"Remembered [{category}]: {content}")
    
    return {
        "response": f"I'll remember that, {USER_NAME}.",
        "content": content,
        "category": category
    }


@skill(
    IntentCategory.MEMORY,
    ["recall", "what_remember"],
    "Recall information"
)
def handle_recall(intent: Intent) -> Dict[str, Any]:
    """Recall stored information"""
    query = intent.entities.get("query", "").strip()
    
    if not query:
        raw = intent.raw_text.lower()
        for trigger in ["remember about", "know about", "recall"]:
            if trigger in raw:
                query = raw.split(trigger, 1)[-1].strip()
                break
    
    memory = get_memory()
    
    if not query:
        # Return all facts
        facts = memory.get_facts()
        if facts:
            fact_list = [f["fact"] for f in facts[:5]]
            return {
                "response": f"Here's what I remember, {USER_NAME}: " + "; ".join(fact_list),
                "facts": fact_list
            }
        else:
            return {
                "response": f"I don't have anything stored in my memory yet, {USER_NAME}.",
                "facts": []
            }
    
    # Search for specific information
    result = memory.recall(query)
    
    if result:
        return {
            "response": f"I remember that {result}",
            "found": result
        }
    else:
        return {
            "response": f"I don't have any information about {query}, {USER_NAME}.",
            "error": "not_found"
        }


@skill(
    IntentCategory.MEMORY,
    ["forget"],
    "Forget/delete information"
)
def handle_forget(intent: Intent) -> Dict[str, Any]:
    """Delete stored information"""
    # For now, just acknowledge - full implementation would search and delete
    return {
        "response": f"I've cleared that from my memory, {USER_NAME}."
    }


# ══════════════════════════════════════════════════════════════════════════════
# GENERAL/FALLBACK - NOW WITH AI!
# ══════════════════════════════════════════════════════════════════════════════

@skill(
    IntentCategory.CONVERSATION,
    ["general", "*"],
    "Handle general conversation with AI"
)
def handle_general(intent: Intent) -> Dict[str, Any]:
    """Handle general/unclassified conversation using AI"""
    from core.ai import get_ai
    
    ai = get_ai()
    raw_text = intent.raw_text
    
    # Try to get AI response
    if ai.is_available():
        try:
            response = ai.chat_response(raw_text)
            return {
                "response": response,
                "ai_powered": True
            }
        except Exception as e:
            logger.error(f"AI response error: {e}")
    
    # Fallback responses if AI is not available
    responses = [
        f"I'm not sure I understand, {USER_NAME}. Could you rephrase that?",
        f"I didn't quite catch that, {USER_NAME}. What would you like me to do?",
        f"I'm not sure how to help with that, {USER_NAME}. Try asking about my capabilities.",
    ]
    return {"response": random.choice(responses), "ai_powered": False}


# Register fallback handler
def fallback_handler(intent: Intent) -> Dict[str, Any]:
    """Fallback for completely unhandled intents - uses AI"""
    from core.ai import get_ai
    
    ai = get_ai()
    raw_text = intent.raw_text
    
    # Try AI response for unknown intents
    if ai.is_available():
        try:
            response = ai.chat_response(raw_text)
            return {
                "response": response,
                "ai_powered": True
            }
        except Exception as e:
            logger.error(f"Fallback AI error: {e}")
    
    return {
        "response": f"I apologize, {USER_NAME}. I'm not sure how to handle that request. "
                   "Try saying 'help' to see what I can do.",
        "ai_powered": False
    }


# Set fallback on module load
get_dispatcher().set_fallback(fallback_handler)
