import pytest
from src.telegram.parser import parse_update

def test_parse_message_with_text():
    update = {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "date": 1600000000,
            "chat": {"id": 123, "title": "Test Chat"},
            "from": {"id": 456, "first_name": "John"},
            "text": "Hello world"
        }
    }
    parsed = parse_update(update)
    assert parsed is not None
    assert parsed.update_id == 1
    assert parsed.message_id == 10
    assert parsed.chat_id == 123
    assert parsed.chat_name == "Test Chat"
    assert parsed.sender_id == 456
    assert parsed.sender_name == "John"
    assert parsed.time == 1600000000
    assert parsed.text == "Hello world"
    assert not parsed.is_edit

def test_parse_edited_message():
    update = {
        "update_id": 2,
        "edited_message": {
            "message_id": 11,
            "date": 1600000000,
            "chat": {"id": 123, "title": "Test Chat"},
            "from": {"id": 456, "first_name": "John"},
            "text": "Edited text"
        }
    }
    parsed = parse_update(update)
    assert parsed is not None
    assert parsed.is_edit
    assert parsed.text == "Edited text"

def test_ignore_media_without_caption():
    update = {
        "update_id": 3,
        "message": {
            "message_id": 12,
            "date": 1600000000,
            "chat": {"id": 123},
            "photo": [{"file_id": "abc"}]
        }
    }
    parsed = parse_update(update)
    assert parsed is None

def test_ignore_service_message():
    update = {
        "update_id": 4,
        "message": {
            "message_id": 13,
            "date": 1600000000,
            "chat": {"id": 123},
            "new_chat_members": [{"id": 789}]
        }
    }
    parsed = parse_update(update)
    assert parsed is None
