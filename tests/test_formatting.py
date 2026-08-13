import pytest
from src.utils.time import format_history
import os

def test_format_history():
    # Force UTC timezone for testing to ensure consistent formatting across environments
    os.environ["TZ"] = "UTC"
    import time
    if hasattr(time, 'tzset'):
        time.tzset()
        
    # Setup test messages spanning two days
    # Format: (sender_id, sender_name, text, time)
    messages = [
        (1, "Alice", "Hello on day 1", 1600000000),  # 2020-09-13 12:26:40 UTC
        (2, "Bob", "Hi Alice", 1600001000),          # 2020-09-13 12:43:20 UTC
        (1, "Alice", "Hello on day 2", 1600100000)   # 2020-09-14 16:13:20 UTC
    ]
    
    formatted = format_history(messages)
    
    # Assertions
    assert "--- 2020-09-13 ---" in formatted
    assert "--- 2020-09-14 ---" in formatted
    
    # Check format "[HH:MM] Имя (ID): текст"
    assert "[12:26] Alice (ID: 1): Hello on day 1" in formatted
    assert "[12:43] Bob (ID: 2): Hi Alice" in formatted
    assert "[16:13] Alice (ID: 1): Hello on day 2" in formatted

def test_format_empty_history():
    assert format_history([]) == "Нет сообщений."
