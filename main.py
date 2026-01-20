#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              JARVIS AI ASSISTANT                             ║
║                        Production-Grade Voice Assistant                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

A sophisticated, modular, event-driven AI assistant for Windows.

Features:
- Wake word detection ("Jarvis")
- Natural speech recognition and synthesis
- Plugin-based skill system
- Persistent memory
- System control capabilities
- Web and application integration

Author: Elite AI Systems Architect
Version: 1.0.0
"""

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Ensure we're running from the correct directory
JARVIS_ROOT = Path(__file__).parent
sys.path.insert(0, str(JARVIS_ROOT))
os.chdir(JARVIS_ROOT)


def setup_logging():
    """Configure logging system"""
    from config import (
        LOG_FILE, LOG_LEVEL, LOG_FORMAT, 
        LOG_DATE_FORMAT, LOG_MAX_SIZE, LOG_BACKUP_COUNT
    )
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (all levels, rotating)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    logging.info("Logging system initialized")


def check_dependencies(text_mode: bool = False):
    """Check if required dependencies are installed"""
    required = [
        ('speech_recognition', 'SpeechRecognition'),
        ('pyttsx3', 'pyttsx3'),
        ('psutil', 'psutil'),
        ('colorama', 'colorama'),
    ]
    
    # PyAudio only required for voice mode
    optional_voice = [
        ('pyaudio', 'pyaudio'),
    ]
    
    missing = []
    
    for module, package in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("\n⚠️  Missing required dependencies:")
        for pkg in missing:
            print(f"   • {pkg}")
        print(f"\nInstall with: pip install {' '.join(missing)}")
        print("Or run: pip install -r requirements.txt\n")
        return False
    
    # Check optional voice dependencies
    if not text_mode:
        voice_missing = []
        for module, package in optional_voice:
            try:
                __import__(module)
            except ImportError:
                voice_missing.append(package)
        
        if voice_missing:
            print("\n⚠️  Voice input unavailable (missing PyAudio)")
            print("   Options:")
            print("   1. Install PyAudio: python install_pyaudio.py")
            print("   2. Run in text mode: python main.py --text\n")
    
    return True


def main():
    """Main entry point"""
    print("\n🔄 Initializing JARVIS...")
    
    # Check dependencies first
    if not check_dependencies(text_mode=False):
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("JARVIS AI Assistant Starting")
    logger.info("=" * 60)
    
    try:
        # Import and start engine
        from core.engine import get_engine
        
        engine = get_engine()
        
        if not engine.initialize():
            logger.error("Engine initialization failed")
            print("\n❌ Failed to initialize JARVIS. Check logs for details.")
            sys.exit(1)
        
        # Start the engine (blocking)
        engine.start()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        print("\n\n👋 Goodbye!")
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


def run_text_mode():
    """Run in text mode (no voice)"""
    print("\n🔄 Starting JARVIS in Text Mode...")
    
    if not check_dependencies(text_mode=True):
        sys.exit(1)
    
    setup_logging()
    
    from core.brain import get_brain
    from core.dispatcher import get_dispatcher
    from core.memory import get_memory
    
    # Import skills
    from skills import system, apps, time_date, web, conversation
    
    brain = get_brain()
    dispatcher = get_dispatcher()
    memory = get_memory()
    
    from colorama import init, Fore, Style
    init()
    
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════╗")
    print(f"║      JARVIS - TEXT MODE ACTIVE          ║")
    print(f"║      Type 'quit' or 'exit' to end       ║")
    print(f"╚══════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    while True:
        try:
            command = input(f"{Fore.GREEN}You:{Style.RESET_ALL} ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print(f"\n{Fore.CYAN}JARVIS:{Style.RESET_ALL} Goodbye, Sir. Until next time.\n")
                break
            
            # Process command
            intent = brain.classify_intent(command)
            result = dispatcher.dispatch(intent)
            
            if result.get("success"):
                handler_result = result.get("result", {})
                if isinstance(handler_result, dict) and handler_result.get("response"):
                    response = handler_result["response"]
                elif isinstance(handler_result, str):
                    response = handler_result
                else:
                    response = brain.generate_response(intent, result)
            else:
                response = brain.generate_response(intent, result)
            
            print(f"{Fore.CYAN}JARVIS:{Style.RESET_ALL} {response}\n")
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}JARVIS:{Style.RESET_ALL} Goodbye!\n")
            break
        except Exception as e:
            print(f"{Fore.RED}Error:{Style.RESET_ALL} {e}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument(
        '--text', '-t',
        action='store_true',
        help='Run in text mode (no voice)'
    )
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        os.environ['JARVIS_DEBUG'] = '1'
    
    if args.text:
        run_text_mode()
    else:
        main()
