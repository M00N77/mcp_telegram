from datetime import datetime, timezone
import zoneinfo
from config import settings

def format_history(messages: list) -> str:
    """Форматирует историю сообщений в Plain Text с разделителями дат."""
    if not messages:
        return "Нет сообщений."
        
    try:
        tz = zoneinfo.ZoneInfo(settings.tz)
    except Exception:
        tz = timezone.utc

    lines = []
    current_date_str = None
    
    for sender_id, sender_name, text, time in messages:
        dt = datetime.fromtimestamp(time, tz=tz)
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M")
        
        if date_str != current_date_str:
            lines.append(f"--- {date_str} ---")
            current_date_str = date_str
            
        lines.append(f"[{time_str}] {sender_name} (ID: {sender_id}): {text}")
        
    return "\n".join(lines)
