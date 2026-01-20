"""
JARVIS Application Management Skills
Launch, close, and manage applications
"""

import os
import subprocess
import psutil
import logging
import webbrowser
from typing import Dict, Any, Optional
from pathlib import Path

from core.dispatcher import skill, get_dispatcher
from core.brain import IntentCategory, Intent
from config import APP_PATHS

logger = logging.getLogger(__name__)

# Web-based applications that should open in browser
WEB_APPS = {
    "youtube": "https://www.youtube.com",
    "netflix": "https://www.netflix.com",
    "prime video": "https://www.primevideo.com",
    "amazon prime": "https://www.primevideo.com",
    "hotstar": "https://www.hotstar.com",
    "disney plus": "https://www.disneyplus.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.x.com",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "telegram": "https://web.telegram.org",
    "gmail": "https://mail.google.com",
    "google mail": "https://mail.google.com",
    "google drive": "https://drive.google.com",
    "drive": "https://drive.google.com",
    "google docs": "https://docs.google.com",
    "google sheets": "https://sheets.google.com",
    "google photos": "https://photos.google.com",
    "github": "https://www.github.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "chatgpt": "https://chat.openai.com",
    "claude": "https://claude.ai",
    "google": "https://www.google.com",
    "wikipedia": "https://www.wikipedia.org",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "outlook": "https://outlook.live.com",
    "spotify web": "https://open.spotify.com",
    "twitch": "https://www.twitch.tv",
    "pinterest": "https://www.pinterest.com",
    "tiktok": "https://www.tiktok.com",
    "snapchat": "https://www.snapchat.com",
    "google meet": "https://meet.google.com",
    "zoom web": "https://zoom.us/join",
    "notion": "https://www.notion.so",
    "trello": "https://trello.com",
    "slack": "https://slack.com",
    "canva": "https://www.canva.com",
    "figma": "https://www.figma.com",
}


def is_web_app(app_name: str) -> Optional[str]:
    """
    Check if app should open in browser
    Returns URL if it's a web app, None otherwise
    """
    app_lower = app_name.lower().strip()
    
    for web_app_name, web_url in WEB_APPS.items():
        if web_app_name in app_lower or app_lower in web_app_name:
            return web_url
    return None


def find_app_path(app_name: str) -> Optional[str]:
    """
    Find application executable path
    
    Searches:
    1. Configured APP_PATHS
    2. Common installation directories
    3. System PATH
    """
    app_lower = app_name.lower().strip()
    
    # FIRST: Check if it's a web app - skip exe search
    if is_web_app(app_lower):
        return None  # Will be handled by web app logic
    
    # Check configured paths
    for name, path in APP_PATHS.items():
        if app_lower in name.lower():
            if os.path.exists(path) or path.startswith("ms-") or not os.path.isabs(path):
                return path
    
    # Common app name variations
    app_variations = {
        "chrome": ["chrome", "google chrome"],
        "firefox": ["firefox", "mozilla firefox"],
        "edge": ["edge", "microsoft edge"],
        "notepad": ["notepad"],
        "calculator": ["calc", "calculator"],
        "code": ["vscode", "vs code", "visual studio code"],
        "word": ["word", "microsoft word", "ms word"],
        "excel": ["excel", "microsoft excel", "ms excel"],
        "powerpoint": ["powerpoint", "ppt", "microsoft powerpoint"],
        "explorer": ["file explorer", "explorer", "files"],
        "cmd": ["command prompt", "cmd", "terminal"],
        "powershell": ["powershell", "ps"],
        "spotify": ["spotify"],
        "discord": ["discord"],
    }
    
    # Check variations
    for exe_name, variations in app_variations.items():
        if any(var in app_lower for var in variations):
            if exe_name in APP_PATHS:
                return APP_PATHS[exe_name]
    
    # Check if it's a direct executable name
    if app_lower.endswith('.exe'):
        return app_lower
    
    # Try adding .exe
    potential_exe = f"{app_lower}.exe"
    
    # Search common directories
    search_dirs = [
        Path(os.environ.get('ProgramFiles', 'C:\\Program Files')),
        Path(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')),
        Path.home() / 'AppData' / 'Local',
        Path.home() / 'AppData' / 'Roaming',
        Path('C:\\Windows\\System32'),
    ]
    
    for search_dir in search_dirs:
        if search_dir.exists():
            # Direct match
            direct = search_dir / potential_exe
            if direct.exists():
                return str(direct)
            
            # Search subdirectories (one level)
            try:
                for subdir in search_dir.iterdir():
                    if subdir.is_dir():
                        potential = subdir / potential_exe
                        if potential.exists():
                            return str(potential)
            except PermissionError:
                continue
    
    # Last resort: try running directly (might be in PATH)
    return potential_exe


def get_running_processes() -> Dict[str, int]:
    """Get dictionary of running process names and PIDs"""
    processes = {}
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            processes[proc.info['name'].lower()] = proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes


@skill(
    IntentCategory.APPLICATION,
    ["open"],
    "Open/launch applications"
)
def handle_app_open(intent: Intent) -> Dict[str, Any]:
    """Open an application"""
    app_name = intent.entities.get("app_name", "").strip()
    
    if not app_name:
        return {
            "response": "Which application would you like me to open?",
            "error": "no_app_specified"
        }
    
    logger.info(f"Opening application: {app_name}")
    app_lower = app_name.lower()
    
    # First check if it's a web-based app
    for web_app_name, web_url in WEB_APPS.items():
        if web_app_name in app_lower or app_lower in web_app_name:
            logger.info(f"Opening web app: {web_app_name} -> {web_url}")
            webbrowser.open(web_url)
            return {
                "response": f"Opening {web_app_name} in your browser.",
                "app": web_app_name,
                "url": web_url,
                "type": "web"
            }
    
    try:
        app_path = find_app_path(app_name)
        
        if not app_path:
            return {
                "response": f"I couldn't find {app_name}. Would you like me to search for it?",
                "error": "app_not_found"
            }
        
        # Handle special paths
        if app_path.startswith("ms-"):
            # Windows Settings URI
            os.startfile(app_path)
        elif " --" in app_path or " /" in app_path:
            # Command with arguments
            subprocess.Popen(app_path, shell=True)
        else:
            # Standard executable
            subprocess.Popen([app_path], shell=True)
        
        logger.info(f"Launched: {app_path}")
        return {
            "response": f"Opening {app_name}.",
            "app": app_name,
            "path": app_path
        }
        
    except FileNotFoundError:
        logger.error(f"Application not found: {app_name}")
        return {
            "response": f"I couldn't find {app_name} on your system.",
            "error": "file_not_found"
        }
    except Exception as e:
        logger.error(f"Failed to open {app_name}: {e}")
        return {
            "response": f"I had trouble opening {app_name}.",
            "error": str(e)
        }


@skill(
    IntentCategory.APPLICATION,
    ["close"],
    "Close applications"
)
def handle_app_close(intent: Intent) -> Dict[str, Any]:
    """Close an application"""
    app_name = intent.entities.get("app_name", "").strip()
    
    if not app_name:
        return {
            "response": "Which application would you like me to close?",
            "error": "no_app_specified"
        }
    
    logger.info(f"Closing application: {app_name}")
    
    try:
        app_lower = app_name.lower()
        closed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                
                # Match process name
                if app_lower in proc_name or proc_name.replace('.exe', '') in app_lower:
                    proc.terminate()
                    closed_count += 1
                    logger.info(f"Terminated: {proc.info['name']} (PID: {proc.info['pid']})")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if closed_count > 0:
            return {
                "response": f"Closed {app_name}.",
                "closed_count": closed_count
            }
        else:
            return {
                "response": f"I couldn't find {app_name} running.",
                "error": "app_not_running"
            }
            
    except Exception as e:
        logger.error(f"Failed to close {app_name}: {e}")
        return {
            "response": f"I had trouble closing {app_name}.",
            "error": str(e)
        }


@skill(
    IntentCategory.APPLICATION,
    ["list", "running"],
    "List running applications"
)
def handle_app_list(intent: Intent) -> Dict[str, Any]:
    """List running applications"""
    try:
        # Get unique application names (not system processes)
        system_processes = {
            'system', 'system idle process', 'csrss.exe', 'smss.exe',
            'wininit.exe', 'services.exe', 'lsass.exe', 'svchost.exe',
            'dwm.exe', 'conhost.exe', 'winlogon.exe', 'fontdrvhost.exe',
            'spoolsv.exe', 'searchindexer.exe', 'audiodg.exe'
        }
        
        apps = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                if name not in system_processes and not name.startswith('svchost'):
                    apps.add(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        app_list = sorted(list(apps))[:10]  # Top 10
        
        return {
            "response": f"Currently running: {', '.join(app_list)}",
            "apps": app_list
        }
        
    except Exception as e:
        logger.error(f"Failed to list apps: {e}")
        return {"error": str(e)}
