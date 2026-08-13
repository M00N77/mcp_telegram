import pytest
import pytest_asyncio
import aiosqlite
import os
from src.db.repository import TelegramRepository

@pytest_asyncio.fixture
async def repo():
    # Use in-memory SQLite database
    conn = await aiosqlite.connect(":memory:")
    
    # Load schema
    schema_path = os.path.join(os.path.dirname(__file__), "..", "src", "db", "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
    
    await conn.executescript(schema)
    await conn.commit()
    
    repository = TelegramRepository(conn)
    yield repository
    
    await repository.close()
    await conn.close()

@pytest.mark.asyncio
async def test_save_message_no_duplicates(repo):
    chat_id = 1
    message_id = 100
    
    # First insert
    await repo.save_message(chat_id, message_id, 2, "Alice", 1600000000, "Hello", False)
    
    # Second insert with same chat_id and message_id (should DO NOTHING)
    await repo.save_message(chat_id, message_id, 2, "Alice", 1600000010, "Hello again", False)
    
    # Verify
    messages = await repo.get_recent_messages(chat_id, 10)
    assert len(messages) == 1
    assert messages[0][2] == "Hello"  # text is unchanged
    assert messages[0][3] == 1600000000  # time is unchanged

@pytest.mark.asyncio
async def test_save_edited_message(repo):
    chat_id = 2
    message_id = 200
    
    # Initial message
    await repo.save_message(chat_id, message_id, 3, "Bob", 1600000000, "Original", False)
    
    # Edit message
    await repo.save_message(chat_id, message_id, 3, "Bob", 1600000050, "Edited", True)
    
    # Verify
    messages = await repo.get_recent_messages(chat_id, 10)
    assert len(messages) == 1
    assert messages[0][2] == "Edited"  # text is updated
    assert messages[0][3] == 1600000000  # time is NOT updated (keeps original order)
