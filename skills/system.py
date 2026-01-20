"""
JARVIS System Control Skills
OS-level operations: shutdown, restart, sleep, lock, volume, screenshots
"""

import os
import subprocess
import ctypes
import logging
from typing import Dict, Any

from core.dispatcher import skill, get_dispatcher
from core.brain import IntentCategory, Intent

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# POWER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@skill(
    IntentCategory.SYSTEM,
    ["shutdown"],
    "Shutdown the computer"
)
def handle_shutdown(intent: Intent) -> Dict[str, Any]:
    """Shutdown the computer"""
    logger.info("Executing system shutdown...")
    
    try:
        # Windows shutdown command (30 second delay for safety)
        os.system("shutdown /s /t 30")
        return {
            "response": "Initiating system shutdown in 30 seconds. Say 'cancel shutdown' to abort.",
            "action": "shutdown_initiated"
        }
    except Exception as e:
        logger.error(f"Shutdown failed: {e}")
        return {"error": str(e)}


@skill(
    IntentCategory.SYSTEM,
    ["restart"],
    "Restart the computer"
)
def handle_restart(intent: Intent) -> Dict[str, Any]:
    """Restart the computer"""
    logger.info("Executing system restart...")
    
    try:
        os.system("shutdown /r /t 30")
        return {
            "response": "Initiating system restart in 30 seconds. Say 'cancel shutdown' to abort.",
            "action": "restart_initiated"
        }
    except Exception as e:
        logger.error(f"Restart failed: {e}")
        return {"error": str(e)}


# SLEEP FUNCTION COMPLETELY REMOVED - Was causing false matches with "hi"


@skill(
    IntentCategory.SYSTEM,
    ["lock"],
    "Lock the computer"
)
def handle_lock(intent: Intent) -> Dict[str, Any]:
    """Lock the computer"""
    logger.info("Locking computer...")
    
    try:
        ctypes.windll.user32.LockWorkStation()
        return {
            "response": "Locking the computer.",
            "action": "lock_initiated"
        }
    except Exception as e:
        logger.error(f"Lock failed: {e}")
        return {"error": str(e)}


@skill(
    IntentCategory.SYSTEM,
    ["screenshot"],
    "Take a screenshot"
)
def handle_screenshot(intent: Intent) -> Dict[str, Any]:
    """Take a screenshot"""
    logger.info("Taking screenshot...")
    
    try:
        import pyautogui
        from datetime import datetime
        from pathlib import Path
        
        # Save to Pictures folder
        pictures_dir = Path.home() / "Pictures" / "Screenshots"
        pictures_dir.mkdir(exist_ok=True)
        
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = pictures_dir / filename
        
        screenshot = pyautogui.screenshot()
        screenshot.save(str(filepath))
        
        logger.info(f"Screenshot saved: {filepath}")
        return {
            "response": f"Screenshot saved to {filepath.name}",
            "action": "screenshot_taken",
            "path": str(filepath)
        }
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return {"error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# VOLUME CONTROL
# ══════════════════════════════════════════════════════════════════════════════

def get_volume_interface():
    """Get Windows audio volume interface"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        return volume
    except Exception as e:
        logger.error(f"Failed to get volume interface: {e}")
        return None


@skill(
    IntentCategory.VOLUME,
    ["up"],
    "Increase volume"
)
def handle_volume_up(intent: Intent) -> Dict[str, Any]:
    """Increase volume by 10%"""
    try:
        volume = get_volume_interface()
        if volume:
            current = volume.GetMasterVolumeLevelScalar()
            new_vol = min(1.0, current + 0.1)
            volume.SetMasterVolumeLevelScalar(new_vol, None)
            
            return {
                "response": f"Volume increased to {int(new_vol * 100)}%",
                "level": int(new_vol * 100)
            }
        else:
            # Fallback to keyboard
            import pyautogui
            pyautogui.press('volumeup', presses=5)
            return {"response": "Volume increased."}
            
    except Exception as e:
        logger.error(f"Volume up failed: {e}")
        return {"error": str(e)}


@skill(
    IntentCategory.VOLUME,
    ["down"],
    "Decrease volume"
)
def handle_volume_down(intent: Intent) -> Dict[str, Any]:
    """Decrease volume by 10%"""
    try:
        volume = get_volume_interface()
        if volume:
            current = volume.GetMasterVolumeLevelScalar()
            new_vol = max(0.0, current - 0.1)
            volume.SetMasterVolumeLevelScalar(new_vol, None)
            
            return {
                "response": f"Volume decreased to {int(new_vol * 100)}%",
                "level": int(new_vol * 100)
            }
        else:
            import pyautogui
            pyautogui.press('volumedown', presses=5)
            return {"response": "Volume decreased."}
            
    except Exception as e:
        logger.error(f"Volume down failed: {e}")
        return {"error": str(e)}


@skill(
    IntentCategory.VOLUME,
    ["mute"],
    "Mute volume"
)
def handle_volume_mute(intent: Intent) -> Dict[str, Any]:
    """Mute system volume"""
    try:
        volume = get_volume_interface()
        if volume:
            volume.SetMute(1, None)
            return {"response": "Volume muted."}
        else:
            import pyautogui
            pyautogui.press('volumemute')
            return {"response": "Volume muted."}
            
    except Exception as e:
        logger.error(f"Mute failed: {e}")
        return {"error": str(e)}


@skill(
    IntentCategory.VOLUME,
    ["unmute"],
    "Unmute volume"
)
def handle_volume_unmute(intent: Intent) -> Dict[str, Any]:
    """Unmute system volume"""
    try:
        volume = get_volume_interface()
        if volume:
            volume.SetMute(0, None)
            return {"response": "Volume unmuted."}
        else:
            import pyautogui
            pyautogui.press('volumemute')
            return {"response": "Volume unmuted."}
            
    except Exception as e:
        logger.error(f"Unmute failed: {e}")
        return {"error": str(e)}


@skill(
    IntentCategory.VOLUME,
    ["set"],
    "Set volume to specific level"
)
def handle_volume_set(intent: Intent) -> Dict[str, Any]:
    """Set volume to specific level"""
    level = intent.entities.get("level", 50)
    level = max(0, min(100, level))
    
    try:
        volume = get_volume_interface()
        if volume:
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            return {
                "response": f"Volume set to {level}%",
                "level": level
            }
        else:
            return {"response": f"Unable to set volume to {level}%"}
            
    except Exception as e:
        logger.error(f"Volume set failed: {e}")
        return {"error": str(e)}
