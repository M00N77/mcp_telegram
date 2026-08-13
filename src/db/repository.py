import aiosqlite
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramRepository:
    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn
        
    async def close(self):
        """Очистка ресурсов репозитория, если потребуется."""
        pass
        
    async def get_offset(self) -> int:
        async with self.conn.execute("SELECT value FROM state WHERE key = 'offset'") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
            
    async def set_offset(self, offset: int):
        await self.conn.execute(
            "INSERT INTO state (key, value) VALUES ('offset', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (offset,)
        )
        await self.conn.commit()

    async def upsert_chat(self, chat_id: int, chat_name: str):
        await self.conn.execute(
            "INSERT INTO chats (chat_id, chat_name) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET chat_name = excluded.chat_name",
            (chat_id, chat_name)
        )
        # Commit occurs either in set_offset (batch) or caller logic

    async def get_known_chats(self) -> list:
        async with self.conn.execute("SELECT chat_id, chat_name FROM chats ORDER BY chat_name") as cursor:
            return await cursor.fetchall()

    async def get_recent_messages(self, chat_id: int, limit: int) -> list:
        async with self.conn.execute(
            """
            SELECT sender_id, sender_name, message_text, time
            FROM messages WHERE chat_id = ?
            ORDER BY time DESC, message_id DESC LIMIT ?
            """,
            (chat_id, limit)
        ) as cursor:
            return await cursor.fetchall()

    async def save_message(self, chat_id: int, message_id: int, sender_id: Optional[int], sender_name: Optional[str], time: int, text: str, is_edit: bool):
        if is_edit:
            await self.conn.execute(
                """
                INSERT INTO messages (chat_id, message_id, sender_id, sender_name, time, message_text)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, message_id) DO UPDATE SET
                    message_text = excluded.message_text,
                    sender_name = excluded.sender_name
                """,
                (chat_id, message_id, sender_id, sender_name, time, text)
            )
        else:
            await self.conn.execute(
                """
                INSERT INTO messages (chat_id, message_id, sender_id, sender_name, time, message_text)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, message_id) DO NOTHING
                """,
                (chat_id, message_id, sender_id, sender_name, time, text)
            )
