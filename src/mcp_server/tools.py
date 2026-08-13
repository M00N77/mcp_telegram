import logging
from typing import Annotated
from pydantic import Field
from .server import mcp
from services.telegram_service import TelegramService

logger = logging.getLogger(__name__)

_service: TelegramService | None = None

def init_tools(service: TelegramService):
    """Инициализация тулов (инъекция зависимости сервиса)."""
    global _service
    _service = service

@mcp.tool()
async def get_known_chats() -> str:
    """Получить список известных чатов (где бот состоит и была активность)."""
    if not _service:
        return "Сервис не инициализирован."
    return await _service.get_known_chats()

@mcp.tool()
async def get_recent_messages(chat_id: int, limit: Annotated[int, Field(ge=1, le=100)] = 20) -> str:
    """Получить последние сообщения из указанного чата.
    
    Args:
        chat_id: Идентификатор чата (число)
        limit: Количество сообщений (от 1 до 100)
    """
    if not _service:
        return "Сервис не инициализирован."
    return await _service.get_recent_messages(chat_id, limit)

@mcp.tool()
async def send_message(chat_id: int, text: str) -> str:
    """Отправить сообщение в указанный чат.
    
    Args:
        chat_id: Идентификатор чата (полученный из get_known_chats)
        text: Текст отправляемого сообщения
    """
    if not _service:
        return "Сервис не инициализирован."
    return await _service.send_message(chat_id, text)
