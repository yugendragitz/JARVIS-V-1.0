"""
JARVIS Speech-to-Text Engine
Continuous listening with wake word detection
"""

import speech_recognition as sr
import threading
import queue
import time
from typing import Optional, Callable, Tuple
import logging

logger = logging.getLogger(__name__)

# Check PyAudio availability
PYAUDIO_AVAILABLE = False
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    logger.warning("PyAudio not available - microphone features disabled")
    logger.warning("Install PyAudio for voice control, or use text mode: python main.py --text")


class STTEngine:
    """
    Advanced Speech-to-Text engine with:
    - Continuous background listening
    - Wake word detection
    - Ambient noise adaptation
    - Multiple recognition backends
    - Error recovery
    """
    
    def __init__(
        self,
        energy_threshold: int = 4000,
        pause_threshold: float = 0.8,
        phrase_time_limit: int = 10,
        timeout: int = 5,
        language: str = "en-US"
    ):
        self._recognizer = sr.Recognizer()
        self._microphone: Optional[sr.Microphone] = None
        self._energy_threshold = energy_threshold
        self._pause_threshold = pause_threshold
        self._phrase_time_limit = phrase_time_limit
        self._timeout = timeout
        self._language = language
        
        self._listen_thread: Optional[threading.Thread] = None
        self._running = False
        self._command_queue: queue.Queue = queue.Queue()
        self._callback: Optional[Callable[[str], None]] = None
        
        # Wake word state
        self._wake_words: list = []
        self._listening_for_command = False
        self._last_wake_time = 0
        self._command_timeout = 30
        
    def initialize(self) -> bool:
        """Initialize the STT engine"""
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio not installed - voice input unavailable")
            logger.error("Run: python main.py --text  for text mode")
            return False
            
        try:
            # Configure recognizer
            self._recognizer.energy_threshold = self._energy_threshold
            self._recognizer.pause_threshold = self._pause_threshold
            self._recognizer.dynamic_energy_threshold = True
            
            # Test microphone access
            self._microphone = sr.Microphone()
            with self._microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info(f"STT Engine initialized. Energy threshold: {self._recognizer.energy_threshold}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize STT: {e}")
            return False
    
    def set_wake_words(self, wake_words: list):
        """Set wake words for activation"""
        self._wake_words = [w.lower() for w in wake_words]
        logger.info(f"Wake words set: {self._wake_words}")
    
    def set_callback(self, callback: Callable[[str], None]):
        """Set callback for when command is recognized"""
        self._callback = callback
    
    def _check_wake_word(self, text: str) -> Tuple[bool, str]:
        """
        Check if text contains wake word and extract command
        
        Returns:
            Tuple of (wake_word_detected, remaining_command)
        """
        text_lower = text.lower().strip()
        
        for wake_word in self._wake_words:
            if text_lower.startswith(wake_word):
                # Extract command after wake word
                command = text_lower[len(wake_word):].strip()
                return True, command
            elif wake_word in text_lower:
                # Wake word somewhere in text
                idx = text_lower.find(wake_word)
                command = text_lower[idx + len(wake_word):].strip()
                return True, command
        
        return False, text
    
    def _listen_worker(self):
        """Background worker for continuous listening"""
        logger.info("Starting continuous listening...")
        
        while self._running:
            try:
                with self._microphone as source:
                    # Periodically recalibrate
                    if time.time() % 60 < 1:
                        self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    try:
                        audio = self._recognizer.listen(
                            source,
                            timeout=self._timeout,
                            phrase_time_limit=self._phrase_time_limit
                        )
                    except sr.WaitTimeoutError:
                        # Check if command mode should timeout
                        if self._listening_for_command:
                            if time.time() - self._last_wake_time > self._command_timeout:
                                self._listening_for_command = False
                                logger.debug("Command mode timed out")
                        continue
                
                # Process audio in background
                threading.Thread(
                    target=self._process_audio,
                    args=(audio,),
                    daemon=True
                ).start()
                
            except Exception as e:
                logger.error(f"Listen worker error: {e}")
                time.sleep(1)  # Prevent rapid error loops
    
    def _process_audio(self, audio: sr.AudioData):
        """Process captured audio"""
        try:
            # Try Google Speech Recognition (free, no API key)
            text = self._recognizer.recognize_google(audio, language=self._language)
            
            if not text:
                return
                
            logger.debug(f"Heard: {text}")
            
            # Check for wake word
            wake_detected, command = self._check_wake_word(text)
            
            if wake_detected:
                self._listening_for_command = True
                self._last_wake_time = time.time()
                
                if command:
                    # Wake word + command in same phrase
                    self._dispatch_command(command)
                else:
                    # Just wake word, waiting for command
                    self._command_queue.put(("WAKE", ""))
                    if self._callback:
                        self._callback("__WAKE__")
            
            elif self._listening_for_command:
                # In command mode, process as command
                if time.time() - self._last_wake_time < self._command_timeout:
                    self._dispatch_command(text)
                else:
                    self._listening_for_command = False
                    
        except sr.UnknownValueError:
            logger.debug("Could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            # Fallback to offline recognition if available
            self._try_offline_recognition(audio)
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
    
    def _try_offline_recognition(self, audio: sr.AudioData):
        """Fallback offline recognition using Sphinx"""
        try:
            text = self._recognizer.recognize_sphinx(audio)
            if text:
                logger.debug(f"Sphinx heard: {text}")
                wake_detected, command = self._check_wake_word(text)
                if wake_detected and command:
                    self._dispatch_command(command)
        except:
            pass  # Sphinx may not be installed
    
    def _dispatch_command(self, command: str):
        """Dispatch recognized command"""
        if not command:
            return
            
        logger.info(f"Command: {command}")
        self._command_queue.put(("COMMAND", command))
        
        if self._callback:
            self._callback(command)
    
    def start_listening(self):
        """Start continuous background listening"""
        if self._running:
            return
            
        self._running = True
        self._listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
        self._listen_thread.start()
        logger.info("Continuous listening started")
    
    def stop_listening(self):
        """Stop listening"""
        self._running = False
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=2.0)
        logger.info("Listening stopped")
    
    def listen_once(self, timeout: int = None) -> Optional[str]:
        """Listen for a single phrase (blocking)"""
        timeout = timeout or self._timeout
        
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=self._phrase_time_limit
                )
                text = self._recognizer.recognize_google(audio, language=self._language)
                return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            logger.error(f"listen_once error: {e}")
            return None
    
    def get_command(self, timeout: float = None) -> Optional[Tuple[str, str]]:
        """Get command from queue"""
        try:
            return self._command_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def clear_queue(self):
        """Clear command queue"""
        while not self._command_queue.empty():
            try:
                self._command_queue.get_nowait()
            except queue.Empty:
                break
    
    def is_listening(self) -> bool:
        """Check if currently listening"""
        return self._running
    
    def recalibrate(self):
        """Recalibrate for ambient noise"""
        try:
            with self._microphone as source:
                logger.info("Recalibrating...")
                self._recognizer.adjust_for_ambient_noise(source, duration=2)
                logger.info(f"New energy threshold: {self._recognizer.energy_threshold}")
        except Exception as e:
            logger.error(f"Recalibration error: {e}")
    
    def shutdown(self):
        """Gracefully shutdown STT engine"""
        logger.info("Shutting down STT engine...")
        self.stop_listening()
        self.clear_queue()
        logger.info("STT engine shutdown complete")


# Global STT instance
_stt_instance: Optional[STTEngine] = None


def get_stt() -> STTEngine:
    """Get or create global STT instance"""
    global _stt_instance
    if _stt_instance is None:
        from config import (
            SR_ENERGY_THRESHOLD, SR_PAUSE_THRESHOLD,
            SR_PHRASE_TIME_LIMIT, SR_TIMEOUT, SR_LANGUAGE, WAKE_WORDS
        )
        _stt_instance = STTEngine(
            energy_threshold=SR_ENERGY_THRESHOLD,
            pause_threshold=SR_PAUSE_THRESHOLD,
            phrase_time_limit=SR_PHRASE_TIME_LIMIT,
            timeout=SR_TIMEOUT,
            language=SR_LANGUAGE
        )
        _stt_instance.initialize()
        _stt_instance.set_wake_words(WAKE_WORDS)
    return _stt_instance
