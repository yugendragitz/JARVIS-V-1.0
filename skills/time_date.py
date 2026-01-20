"""
JARVIS Time and Date Skills
Time, date, timers, alarms
"""

from datetime import datetime, timedelta
import logging
from typing import Dict, Any

from core.dispatcher import skill, get_dispatcher
from core.brain import IntentCategory, Intent

logger = logging.getLogger(__name__)


@skill(
    IntentCategory.TIME_DATE,
    ["time"],
    "Get current time"
)
def handle_time(intent: Intent) -> Dict[str, Any]:
    """Get current time"""
    now = datetime.now()
    
    # Format time naturally
    hour = now.hour
    minute = now.minute
    
    # 12-hour format with AM/PM
    period = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    
    if minute == 0:
        time_str = f"{hour_12} {period}"
    elif minute == 30:
        time_str = f"half past {hour_12}"
    elif minute == 15:
        time_str = f"quarter past {hour_12}"
    elif minute == 45:
        next_hour = (hour_12 % 12) + 1
        time_str = f"quarter to {next_hour}"
    else:
        time_str = f"{hour_12}:{minute:02d} {period}"
    
    return {
        "response": f"The time is {time_str}.",
        "time": now.strftime("%H:%M:%S"),
        "formatted": time_str
    }


@skill(
    IntentCategory.TIME_DATE,
    ["date", "today", "day"],
    "Get current date"
)
def handle_date(intent: Intent) -> Dict[str, Any]:
    """Get current date"""
    now = datetime.now()
    
    # Get day of week
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = days[now.weekday()]
    
    # Get month name
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    month_name = months[now.month - 1]
    
    # Ordinal suffix
    day = now.day
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    
    date_str = f"{day_name}, {month_name} {day}{suffix}, {now.year}"
    
    return {
        "response": f"Today is {date_str}.",
        "date": now.strftime("%Y-%m-%d"),
        "formatted": date_str
    }


@skill(
    IntentCategory.TIME_DATE,
    ["datetime", "now"],
    "Get current date and time"
)
def handle_datetime(intent: Intent) -> Dict[str, Any]:
    """Get current date and time"""
    now = datetime.now()
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = days[now.weekday()]
    
    hour = now.hour
    period = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    
    datetime_str = f"{day_name}, {now.strftime('%B')} {now.day}, {now.year}, {hour_12}:{now.minute:02d} {period}"
    
    return {
        "response": f"It's currently {datetime_str}.",
        "datetime": now.isoformat(),
        "formatted": datetime_str
    }
