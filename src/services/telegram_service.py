import logging
from db.repository import TelegramRepository
from telegram.client import TelegramClient
from utils.time import format_history

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self, repo: TelegramRepository, client: TelegramClient):
        self.repo = repo
        self.client = client
        
    async def get_known_chats(self) -> str:
        chats = await self.repo.get_known_chats()
        if not chats:
            return "Нет известных чатов."
        return "\n".join([f"{name} (ID: {chat_id})" for chat_id, name in chats])
        
    async def get_recent_messages(self, chat_id: int, limit: int = 20) -> str:
        # Выборка в обратном порядке по времени (новые сначала)
        messages_desc = await self.repo.get_recent_messages(chat_id, limit)
        # Разворот в прямой хронологический порядок для удобства LLM
        messages_asc = list(reversed(messages_desc))
        return format_history(messages_asc)
        
    async def send_message(self, chat_id: int, text: str) -> str:
        try:
            result = await self.client.send_message(chat_id, text)
            msg_id = result.get("message_id")
            logger.info(f"Message sent to {chat_id}, id={msg_id}")
            return f"Сообщение успешно отправлено. ID: {msg_id}"
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return f"Ошибка при отправке сообщения: {str(e)}"
