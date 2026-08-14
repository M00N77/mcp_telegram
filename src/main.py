import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from utils.logging import setup_logging
from db.database import init_db, close_db
from db.repository import TelegramRepository
from telegram.client import TelegramClient
from telegram.listener import TelegramListener

from services.telegram_service import TelegramService
from mcp_server.server import mcp
from mcp_server.tools import init_tools

logger = logging.getLogger(__name__)

class AppState:
    def __init__(self):
        self.running = False
        self.listener_task = None
        self.watchdog_task = None

async def watchdog(listener: TelegramListener, app_state: AppState):
    """Воскрешает listener, если он умер при работающем приложении."""
    while app_state.running:
        if app_state.listener_task and app_state.listener_task.done() and app_state.running:
            if getattr(listener, "fatal_error", False):
                logger.error("Listener died due to a fatal error (401). Watchdog stopping.")
                break
            logger.error("Listener task died unexpectedly! Restarting...")
            app_state.listener_task = asyncio.create_task(listener.start())
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app_state: AppState):
    """Инициализация и очистка ресурсов приложения."""
    setup_logging()
    logger.info("Starting up Telegram MCP Server (Milestone 3)...")
    logger.info(f"Using database path: {settings.db_path}")
    
    conn = await init_db(settings.db_path)
    repo = TelegramRepository(conn)
    client = TelegramClient(settings.telegram_bot_token)
    await client.start()
    
    try:
        from telegram.client import TelegramUnauthorizedError, TelegramBadRequestError
        await client.get_me()
        await client.delete_webhook()
    except (TelegramUnauthorizedError, TelegramBadRequestError):
        sys.stderr.write("Неверный TELEGRAM_BOT_TOKEN: сервер остановлен\n")
        await client.close()
        await close_db(conn)
        sys.exit(1)
    
    listener = TelegramListener(client, repo)
    app_state.running = True
    
    app_state.listener_task = asyncio.create_task(listener.start())
    app_state.watchdog_task = asyncio.create_task(watchdog(listener, app_state))
    
    try:
        yield repo, client
    finally:
        logger.info("Shutting down gracefully...")
        app_state.running = False
        listener.stop()
        
        if app_state.listener_task:
            app_state.listener_task.cancel()
        if app_state.watchdog_task:
            app_state.watchdog_task.cancel()
            
        await asyncio.gather(app_state.listener_task, app_state.watchdog_task, return_exceptions=True)
        
        if repo:
            await repo.close()
        await client.close()
        await close_db(conn)

async def main():
    app_state = AppState()
    async with lifespan(app_state) as (repo, client):
        logger.info("Server is running. MCP stdio transport started.")
        try:
            service = TelegramService(repo, client)
            init_tools(service)
            
            # Start FastMCP stdio server (blocks until interrupted)
            await mcp.run_stdio_async()
            
        except asyncio.CancelledError:
            logger.info("Main loop cancelled.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, exiting...")
        pass
