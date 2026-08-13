from mcp.server.fastmcp import FastMCP
import logging

logger = logging.getLogger(__name__)

# Создаем инстанс сервера FastMCP.
# Имя сервера и список зависимостей.
mcp = FastMCP("TelegramBotMCP", log_level="ERROR")
