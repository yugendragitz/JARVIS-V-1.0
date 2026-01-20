"""
JARVIS Web Skills
Web search, website navigation, YouTube
"""

import webbrowser
import urllib.parse
import logging
from typing import Dict, Any

from core.dispatcher import skill, get_dispatcher
from core.brain import IntentCategory, Intent

logger = logging.getLogger(__name__)


@skill(
    IntentCategory.WEB,
    ["search"],
    "Search the web"
)
def handle_web_search(intent: Intent) -> Dict[str, Any]:
    """Perform a web search"""
    query = intent.entities.get("query", "").strip()
    
    if not query:
        # Use the raw text if no query extracted
        raw = intent.raw_text.lower()
        for trigger in ["search for", "search", "google", "look up", "find"]:
            if trigger in raw:
                query = raw.split(trigger, 1)[-1].strip()
                break
    
    if not query:
        return {
            "response": "What would you like me to search for?",
            "error": "no_query"
        }
    
    logger.info(f"Web search: {query}")
    
    try:
        # URL encode the query
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        webbrowser.open(search_url)
        
        return {
            "response": f"Searching for {query}.",
            "query": query,
            "url": search_url
        }
        
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return {"error": str(e)}


@skill(
    IntentCategory.WEB,
    ["open", "website", "site"],
    "Open a website"
)
def handle_web_open(intent: Intent) -> Dict[str, Any]:
    """Open a website"""
    raw_text = intent.raw_text.lower()
    
    # Extract URL or site name
    url = None
    
    # Check for common sites
    common_sites = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "facebook": "https://www.facebook.com",
        "twitter": "https://www.twitter.com",
        "x": "https://www.x.com",
        "instagram": "https://www.instagram.com",
        "linkedin": "https://www.linkedin.com",
        "github": "https://www.github.com",
        "reddit": "https://www.reddit.com",
        "amazon": "https://www.amazon.com",
        "netflix": "https://www.netflix.com",
        "gmail": "https://mail.google.com",
        "outlook": "https://outlook.live.com",
        "wikipedia": "https://www.wikipedia.org",
        "stackoverflow": "https://stackoverflow.com",
        "chatgpt": "https://chat.openai.com",
    }
    
    for site, site_url in common_sites.items():
        if site in raw_text:
            url = site_url
            break
    
    # Check if URL is directly mentioned
    if not url:
        import re
        url_match = re.search(r'(https?://\S+|www\.\S+|\S+\.(com|org|net|io|co|edu|gov))', raw_text)
        if url_match:
            url = url_match.group()
            if not url.startswith('http'):
                url = 'https://' + url
    
    if not url:
        return {
            "response": "Which website would you like me to open?",
            "error": "no_url"
        }
    
    logger.info(f"Opening website: {url}")
    
    try:
        webbrowser.open(url)
        
        # Extract site name for response
        site_name = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        
        return {
            "response": f"Opening {site_name}.",
            "url": url
        }
        
    except Exception as e:
        logger.error(f"Failed to open website: {e}")
        return {"error": str(e)}


@skill(
    IntentCategory.WEB,
    ["youtube"],
    "Search or play YouTube"
)
def handle_youtube(intent: Intent) -> Dict[str, Any]:
    """Search or play YouTube"""
    query = intent.entities.get("query", "").strip()
    
    if not query:
        raw = intent.raw_text.lower()
        for trigger in ["play", "youtube", "watch", "search youtube for"]:
            if trigger in raw:
                query = raw.split(trigger, 1)[-1].strip()
                # Clean up common phrases
                query = query.replace("on youtube", "").replace("video", "").strip()
                break
    
    if not query:
        # Just open YouTube
        webbrowser.open("https://www.youtube.com")
        return {
            "response": "Opening YouTube.",
            "url": "https://www.youtube.com"
        }
    
    logger.info(f"YouTube search: {query}")
    
    try:
        encoded_query = urllib.parse.quote_plus(query)
        youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        webbrowser.open(youtube_url)
        
        return {
            "response": f"Searching YouTube for {query}.",
            "query": query,
            "url": youtube_url
        }
        
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
        return {"error": str(e)}


@skill(
    IntentCategory.WEB,
    ["weather"],
    "Check weather"
)
def handle_weather(intent: Intent) -> Dict[str, Any]:
    """Check weather (opens weather website)"""
    raw_text = intent.raw_text.lower()
    
    # Try to extract location
    location = ""
    for trigger in ["weather in", "weather for", "weather at"]:
        if trigger in raw_text:
            location = raw_text.split(trigger, 1)[-1].strip()
            break
    
    if location:
        encoded_loc = urllib.parse.quote_plus(location)
        url = f"https://www.google.com/search?q=weather+{encoded_loc}"
    else:
        url = "https://www.google.com/search?q=weather"
    
    try:
        webbrowser.open(url)
        
        if location:
            return {
                "response": f"Checking the weather for {location}.",
                "location": location,
                "url": url
            }
        else:
            return {
                "response": "Checking the weather for your location.",
                "url": url
            }
            
    except Exception as e:
        logger.error(f"Weather check failed: {e}")
        return {"error": str(e)}
