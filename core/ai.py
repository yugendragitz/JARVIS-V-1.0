"""
JARVIS AI Module
Google Gemini integration for intelligent conversations
"""

import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Run: pip install google-generativeai")


class JarvisAI:
    """
    AI-powered conversation handler using Google Gemini
    handling evvironments with cable + connections of gemini ai powered 2.5 
    
    Features:
    - Intelligent responses like ChatGPT
    - Context-aware conversations
    - Free to use with API key
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model = None
        self.chat = None
        self.conversation_history: List[Dict[str, str]] = []
        self.is_initialized = False
        
        if self.api_key and GEMINI_AVAILABLE:
            self._initialize()
        else:
            if not GEMINI_AVAILABLE:
                logger.warning("Gemini AI not available - install google-generativeai")
            if not self.api_key:
                logger.warning("No API key found. Set GEMINI_API_KEY environment variable for AI features.")
    
    def _initialize(self):
        """Initialize Gemini AI"""
        try:
            genai.configure(api_key=self.api_key)
            
            # Use Gemini 1.5 Flash for fast responses
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=self._get_system_prompt()
            )
            
            # Start a chat session for context
            self.chat = self.model.start_chat(history=[])
            self.is_initialized = True
            logger.info("Gemini AI initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.is_initialized = False
    
    def _get_system_prompt(self) -> str:
        """System prompt for JARVIS personality"""
        return """You are JARVIS, an advanced AI assistant inspired by Iron Man's AI.

Your personality:
- Professional yet warm and helpful
- Intelligent and knowledgeable
- Concise but thorough when needed
- Occasionally witty with subtle humor
- Address the user as "Sir" occasionally

Guidelines:
- Keep responses conversational and natural
- For simple questions, give brief answers (1-2 sentences)
- For complex topics, provide clear explanations
- If asked about capabilities, mention you can help with applications, web searches, system control, etc.
- Always be helpful and proactive
- Don't mention you're an AI unless directly asked
- Never say you can't help - always try to provide useful information"""

    def chat_response(self, message: str) -> str:
        """
        Get an AI response to a message
        
        Args:
            message: User's message
            
        Returns:
            AI generated response
        """
        if not self.is_initialized:
            return self._fallback_response(message)
        
        try:
            # Send message and get response
            response = self.chat.send_message(message)
            
            # Extract text from response
            ai_response = response.text.strip()
            
            # Store in history
            self.conversation_history.append({
                "user": message,
                "assistant": ai_response
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-10:]
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Provide a response when AI is not available"""
        message_lower = message.lower()
        
        # Handle common queries without AI
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "Hello! How can I assist you today?"
        
        if "how are you" in message_lower:
            return "I'm functioning optimally, Sir. How can I help you?"
        
        if any(word in message_lower for word in ["thank", "thanks"]):
            return "You're welcome! Happy to help."
        
        if "who are you" in message_lower or "what are you" in message_lower:
            return ("I'm JARVIS, your personal AI assistant. I can help you with "
                   "opening applications, searching the web, controlling your system, and more.")
        
        if "what can you do" in message_lower or "help" in message_lower:
            return ("I can help you with many things: open applications, search the web, "
                   "play YouTube videos, control system volume, tell you the time, "
                   "take screenshots, and answer questions. Just ask!")
        
        # For other queries, suggest getting the API key
        if not self.api_key:
            return ("I understand your question, but for detailed AI-powered responses, "
                   "please set up a free Gemini API key. You can get one at "
                   "https://makersuite.google.com/app/apikey and set it as GEMINI_API_KEY "
                   "environment variable.")
        
        return ("I'm having trouble processing that right now. "
               "Could you try rephrasing your question?")
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        if self.is_initialized:
            self.chat = self.model.start_chat(history=[])
        logger.info("Conversation history reset")
    
    def is_available(self) -> bool:
        """Check if AI is available"""
        return self.is_initialized


# Global AI instance
_ai_instance: Optional[JarvisAI] = None


def get_ai() -> JarvisAI:
    """Get or create global AI instance"""
    global _ai_instance
    if _ai_instance is None:
        # Try to get API key from config or environment
        from config import settings
        api_key = getattr(settings, 'GEMINI_API_KEY', None) if hasattr(settings, 'GEMINI_API_KEY') else None
        _ai_instance = JarvisAI(api_key=api_key)
    return _ai_instance


def chat(message: str) -> str:
    """Convenience function for quick chat"""
    return get_ai().chat_response(message)
