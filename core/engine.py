"""
JARVIS Main Engine
Central runtime loop and orchestration
"""

import time
import threading
import signal
import sys
import logging
from typing import Optional, Callable
from enum import Enum, auto
from datetime import datetime
import random

from .brain import Brain, get_brain, Intent, IntentCategory
from .dispatcher import Dispatcher, get_dispatcher
from .memory import Memory, get_memory

logger = logging.getLogger(__name__)


class EngineState(Enum):
    """Engine operational states"""
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    STOPPING = auto()


class Engine:
    """
    JARVIS Main Engine
    
    Orchestrates:
    - Audio input/output
    - Intent processing
    - Skill execution
    - State management
    - Graceful lifecycle
    """
    
    def __init__(self):
        self._state = EngineState.STOPPED
        self._running = False
        self._brain: Optional[Brain] = None
        self._dispatcher: Optional[Dispatcher] = None
        self._memory: Optional[Memory] = None
        
        # Audio components (lazy loaded)
        self._tts = None
        self._stt = None
        self._voice_enabled = True
        
        # Callbacks
        self._on_wake: Optional[Callable] = None
        self._on_command: Optional[Callable] = None
        self._on_response: Optional[Callable] = None
        
        # Thread safety
        self._lock = threading.Lock()
        
    @property
    def state(self) -> EngineState:
        return self._state
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def initialize(self) -> bool:
        """Initialize all engine components"""
        self._state = EngineState.STARTING
        logger.info("Initializing JARVIS Engine...")
        
        try:
            # Initialize core components
            self._brain = get_brain()
            self._dispatcher = get_dispatcher()
            self._memory = get_memory()
            
            # Initialize audio
            from audio import get_tts, get_stt
            self._tts = get_tts()
            self._stt = get_stt()
            
            # Check if STT initialized properly
            if not self._stt.is_listening():
                # STT didn't start - likely no PyAudio
                self._voice_enabled = False
                logger.warning("Voice input not available - STT initialization failed")
            else:
                self._voice_enabled = True
            
            # Register skills
            self._register_skills()
            
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            logger.info("JARVIS Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            self._state = EngineState.STOPPED
            return False
    
    def _register_skills(self):
        """Register all skill modules"""
        # Import skill modules to trigger registration
        try:
            from skills import system, apps, time_date, web, conversation
            logger.info("Skills registered successfully")
        except Exception as e:
            logger.error(f"Failed to register skills: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown()
    
    def start(self):
        """Start the engine"""
        if self._running:
            logger.warning("Engine already running")
            return
        
        self._running = True
        self._state = EngineState.RUNNING
        
        # Display startup banner
        self._display_banner()
        
        # Speak startup message
        from config import USER_NAME
        self._tts.speak(f"Jarvis online. Good to see you, {USER_NAME}.", block=True)
        
        # Check if voice is available
        if not self._stt._microphone:
            # No microphone - try to initialize
            if not self._stt.initialize():
                logger.warning("Voice input unavailable - falling back to text mode")
                self._voice_enabled = False
                self._tts.speak("Voice input unavailable. Switching to text mode.", block=True)
                self._run_text_mode()
                return
        
        # Set up STT callback
        self._stt.set_callback(self._on_speech)
        
        # Start listening
        self._stt.start_listening()
        self._state = EngineState.LISTENING
        
        logger.info("JARVIS is now listening...")
        
        # Main loop
        self._main_loop()
    
    def _display_banner(self):
        """Display startup banner"""
        from colorama import init, Fore, Style
        init()
        
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                                  ║
║      ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗                    ║
║      ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝                    ║
║      ██║███████║██████╔╝██║   ██║██║███████╗                    ║
║ ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║                    ║
║ ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║                    ║
║  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝                    ║
║                                                                  ║
║          {Fore.GREEN}[ JARVIS AI ASSISTANT - ONLINE ]{Fore.CYAN}                     ║
║                                                                  ║
║  {Fore.YELLOW}• Wake Word:{Fore.WHITE} "Jarvis"                                       {Fore.CYAN}║
║  {Fore.YELLOW}• Status:{Fore.WHITE} All systems operational                           {Fore.CYAN}║
║  {Fore.YELLOW}• Time:{Fore.WHITE} {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                               {Fore.CYAN}║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(banner)
        
        # Print registered skills
        skills = self._dispatcher.get_registered_skills()
        print(f"{Fore.GREEN}Loaded Skills:{Style.RESET_ALL}")
        for skill in skills:
            print(f"  {Fore.CYAN}•{Style.RESET_ALL} {skill['name']} - {skill['description']}")
        print()
    
    def _main_loop(self):
        """Main engine loop"""
        while self._running:
            try:
                # Check for commands in queue
                result = self._stt.get_command(timeout=0.5)
                
                if result:
                    event_type, data = result
                    
                    if event_type == "WAKE":
                        self._handle_wake()
                    elif event_type == "COMMAND":
                        self._handle_command(data)
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(1)
        
        self.shutdown()
    
    def _on_speech(self, text: str):
        """Callback when speech is recognized"""
        if text == "__WAKE__":
            # Wake word detected, waiting for command
            pass
        else:
            # Command received
            logger.info(f"Speech recognized: {text}")
    
    def _handle_wake(self):
        """Handle wake word detection"""
        self._state = EngineState.LISTENING
        
        from config import RESPONSES, USER_NAME
        response = random.choice(RESPONSES["greeting"]).replace("{user}", USER_NAME)
        self._tts.speak(response)
        
        if self._on_wake:
            self._on_wake()
    
    def _handle_command(self, command: str):
        """Handle recognized command"""
        self._state = EngineState.PROCESSING
        
        try:
            # Store in conversation history
            self._memory.add_conversation("user", command)
            
            # Classify intent
            intent = self._brain.classify_intent(command)
            logger.info(f"Intent: {intent.category.name}.{intent.action} ({intent.confidence:.1f}%)")
            
            # Check for stop/cancel
            if intent.action == "stop":
                self._tts.clear_queue()
                self._tts.speak("Okay.")
                self._state = EngineState.LISTENING
                return
            
            # Dispatch to handler
            result = self._dispatcher.dispatch(intent)
            
            # Generate and speak response
            self._state = EngineState.SPEAKING
            
            if result.get("success"):
                handler_result = result.get("result", {})
                
                # Check if handler provided a response
                if isinstance(handler_result, dict) and handler_result.get("response"):
                    response = handler_result["response"]
                elif isinstance(handler_result, str):
                    response = handler_result
                else:
                    response = self._brain.generate_response(intent, result)
                
                self._tts.speak(response)
                self._memory.add_conversation("assistant", response, intent.action)
            else:
                # Error or no handler
                if intent.category == IntentCategory.UNKNOWN:
                    from config import RESPONSES, USER_NAME
                    response = random.choice(RESPONSES["not_understood"]).replace("{user}", USER_NAME)
                else:
                    response = self._brain.generate_response(intent, result)
                
                self._tts.speak(response)
            
            if self._on_response:
                self._on_response(response)
                
        except Exception as e:
            logger.error(f"Command handling error: {e}")
            self._tts.speak("I encountered an error processing that request.")
        
        finally:
            self._state = EngineState.LISTENING
    
    def process_text_command(self, command: str):
        """Process a text command (for testing without voice)"""
        self._handle_command(command)
    
    def speak(self, text: str):
        """Speak text through TTS"""
        if self._tts:
            self._tts.speak(text)
    
    def shutdown(self):
        """Gracefully shutdown the engine"""
        if self._state == EngineState.STOPPING:
            return
            
        self._state = EngineState.STOPPING
        self._running = False
        
        logger.info("Shutting down JARVIS...")
        
        from config import USER_NAME
        if self._tts:
            self._tts.speak_immediate(f"Shutting down. Goodbye, {USER_NAME}.")
        
        # Shutdown components
        if self._stt:
            self._stt.shutdown()
        if self._tts:
            self._tts.shutdown()
        if self._memory:
            self._memory.shutdown()
        
        self._state = EngineState.STOPPED
        logger.info("JARVIS shutdown complete")
        
        print("\n[JARVIS OFFLINE]")
    
    def _run_text_mode(self):
        """Run in text-only mode when voice is unavailable"""
        from colorama import Fore, Style
        
        print(f"\n{Fore.YELLOW}📝 Running in TEXT MODE (no microphone){Style.RESET_ALL}")
        print(f"{Fore.CYAN}Type your commands below. Type 'quit' to exit.{Style.RESET_ALL}\n")
        
        while self._running:
            try:
                command = input(f"{Fore.GREEN}You:{Style.RESET_ALL} ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                    break
                
                self._handle_command(command)
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Text mode error: {e}")
        
        self.shutdown()


# Global engine instance
_engine_instance: Optional[Engine] = None


def get_engine() -> Engine:
    """Get or create global engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = Engine()
    return _engine_instance
