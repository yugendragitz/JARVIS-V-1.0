"""
JARVIS Command Dispatcher
Routes intents to appropriate skill handlers
"""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
import logging
import importlib
import inspect

from .brain import Intent, IntentCategory

logger = logging.getLogger(__name__)


@dataclass
class SkillHandler:
    """Represents a registered skill handler"""
    name: str
    category: IntentCategory
    actions: List[str]
    handler: Callable
    description: str = ""


class Dispatcher:
    """
    Command dispatcher that routes intents to skill handlers
    
    Features:
    - Dynamic skill registration
    - Category-based routing
    - Action pattern matching
    - Fallback handling
    """
    
    def __init__(self):
        self._handlers: Dict[str, SkillHandler] = {}
        self._category_handlers: Dict[IntentCategory, List[str]] = {}
        self._fallback: Optional[Callable] = None
        
    def register(
        self,
        name: str,
        category: IntentCategory,
        actions: List[str],
        handler: Callable,
        description: str = ""
    ):
        """
        Register a skill handler
        
        Args:
            name: Unique handler name
            category: Intent category this handler serves
            actions: List of actions this handler can process
            handler: Callable that processes the intent
            description: Human-readable description
        """
        skill = SkillHandler(
            name=name,
            category=category,
            actions=actions,
            handler=handler,
            description=description
        )
        
        self._handlers[name] = skill
        
        # Index by category
        if category not in self._category_handlers:
            self._category_handlers[category] = []
        self._category_handlers[category].append(name)
        
        logger.info(f"Registered skill: {name} [{category.name}] - {actions}")
    
    def register_decorator(
        self,
        category: IntentCategory,
        actions: List[str],
        description: str = ""
    ):
        """Decorator for registering skill handlers"""
        def decorator(func: Callable):
            name = func.__name__
            self.register(name, category, actions, func, description)
            return func
        return decorator
    
    def set_fallback(self, handler: Callable):
        """Set fallback handler for unmatched intents"""
        self._fallback = handler
        logger.info("Fallback handler registered")
    
    def dispatch(self, intent: Intent) -> Dict[str, Any]:
        """
        Dispatch an intent to the appropriate handler
        
        Args:
            intent: Classified intent to dispatch
            
        Returns:
            Result dictionary from handler
        """
        logger.debug(f"Dispatching: {intent.category.name}.{intent.action}")
        
        # Find handlers for this category
        handler_names = self._category_handlers.get(intent.category, [])
        
        for name in handler_names:
            skill = self._handlers[name]
            
            # Check if this skill handles the action
            if intent.action in skill.actions or "*" in skill.actions:
                try:
                    result = skill.handler(intent)
                    return {
                        "success": True,
                        "handler": name,
                        "result": result
                    }
                except Exception as e:
                    logger.error(f"Handler {name} error: {e}")
                    return {
                        "success": False,
                        "handler": name,
                        "error": str(e)
                    }
        
        # Try fallback
        if self._fallback:
            try:
                result = self._fallback(intent)
                return {
                    "success": True,
                    "handler": "fallback",
                    "result": result
                }
            except Exception as e:
                logger.error(f"Fallback handler error: {e}")
        
        # No handler found
        logger.warning(f"No handler for: {intent.category.name}.{intent.action}")
        return {
            "success": False,
            "error": "No handler found"
        }
    
    def get_registered_skills(self) -> List[Dict]:
        """Get list of registered skills"""
        return [
            {
                "name": skill.name,
                "category": skill.category.name,
                "actions": skill.actions,
                "description": skill.description
            }
            for skill in self._handlers.values()
        ]
    
    def unregister(self, name: str):
        """Unregister a skill handler"""
        if name in self._handlers:
            skill = self._handlers[name]
            
            # Remove from category index
            if skill.category in self._category_handlers:
                self._category_handlers[skill.category].remove(name)
            
            del self._handlers[name]
            logger.info(f"Unregistered skill: {name}")


# Global dispatcher instance
_dispatcher_instance: Optional[Dispatcher] = None


def get_dispatcher() -> Dispatcher:
    """Get or create global dispatcher instance"""
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = Dispatcher()
    return _dispatcher_instance


def skill(category: IntentCategory, actions: List[str], description: str = ""):
    """
    Decorator for registering skill handlers
    
    Usage:
        @skill(IntentCategory.SYSTEM, ["shutdown", "restart"])
        def handle_power(intent):
            ...
    """
    return get_dispatcher().register_decorator(category, actions, description)
