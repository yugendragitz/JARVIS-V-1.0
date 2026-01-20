"""
JARVIS Text-to-Speech Engine
High-performance, non-blocking TTS with voice customization
"""

import pyttsx3
import threading
import queue
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Advanced Text-to-Speech engine with:
    - Non-blocking speech queue
    - Voice customization
    - Rate/volume control
    - Graceful error handling
    """
    
    def __init__(self, rate: int = 175, volume: float = 1.0, voice_index: int = 0):
        self._engine: Optional[pyttsx3.Engine] = None
        self._rate = rate
        self._volume = volume
        self._voice_index = voice_index
        self._speech_queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        
    def initialize(self) -> bool:
        """Initialize the TTS engine"""
        try:
            self._engine = pyttsx3.init()
            self._configure_voice()
            self._running = True
            self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self._worker_thread.start()
            logger.info("TTS Engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            return False
    
    def _configure_voice(self):
        """Configure voice properties"""
        if not self._engine:
            return
            
        self._engine.setProperty('rate', self._rate)
        self._engine.setProperty('volume', self._volume)
        
        voices = self._engine.getProperty('voices')
        if voices and len(voices) > self._voice_index:
            self._engine.setProperty('voice', voices[self._voice_index].id)
            logger.debug(f"Voice set to: {voices[self._voice_index].name}")
    
    def _speech_worker(self):
        """Background worker that processes speech queue"""
        while self._running:
            try:
                text = self._speech_queue.get(timeout=0.5)
                if text is None:  # Poison pill
                    break
                self._speak_sync(text)
                self._speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Speech worker error: {e}")
    
    def _speak_sync(self, text: str):
        """Synchronously speak text (internal use)"""
        with self._lock:
            if self._engine:
                try:
                    self._engine.say(text)
                    self._engine.runAndWait()
                except Exception as e:
                    logger.error(f"TTS speak error: {e}")
    
    def speak(self, text: str, block: bool = False):
        """
        Speak text
        
        Args:
            text: Text to speak
            block: If True, wait for speech to complete
        """
        if not text:
            return
            
        logger.debug(f"Speaking: {text}")
        
        if block:
            self._speak_sync(text)
        else:
            self._speech_queue.put(text)
    
    def speak_immediate(self, text: str):
        """Clear queue and speak immediately"""
        self.clear_queue()
        self.speak(text, block=True)
    
    def clear_queue(self):
        """Clear pending speech"""
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
            except queue.Empty:
                break
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        self._rate = rate
        if self._engine:
            self._engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        self._volume = max(0.0, min(1.0, volume))
        if self._engine:
            self._engine.setProperty('volume', self._volume)
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if self._engine:
            return self._engine.getProperty('voices')
        return []
    
    def set_voice(self, voice_index: int):
        """Set voice by index"""
        voices = self.get_available_voices()
        if voices and 0 <= voice_index < len(voices):
            self._voice_index = voice_index
            self._engine.setProperty('voice', voices[voice_index].id)
            logger.info(f"Voice changed to: {voices[voice_index].name}")
    
    def shutdown(self):
        """Gracefully shutdown TTS engine"""
        logger.info("Shutting down TTS engine...")
        self._running = False
        self._speech_queue.put(None)  # Poison pill
        
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        
        if self._engine:
            try:
                self._engine.stop()
            except:
                pass
            self._engine = None
        
        logger.info("TTS engine shutdown complete")


# Global TTS instance
_tts_instance: Optional[TTSEngine] = None


def get_tts() -> TTSEngine:
    """Get or create global TTS instance"""
    global _tts_instance
    if _tts_instance is None:
        from config import TTS_RATE, TTS_VOLUME, TTS_VOICE_INDEX
        _tts_instance = TTSEngine(
            rate=TTS_RATE,
            volume=TTS_VOLUME,
            voice_index=TTS_VOICE_INDEX
        )
        _tts_instance.initialize()
    return _tts_instance


def speak(text: str, block: bool = False):
    """Convenience function to speak text"""
    get_tts().speak(text, block)


def speak_immediate(text: str):
    """Convenience function to speak immediately"""
    get_tts().speak_immediate(text)
