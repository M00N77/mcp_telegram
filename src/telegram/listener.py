import asyncio
import logging
from .client import TelegramClient, TelegramAPIError, TelegramRateLimitError, TelegramUnauthorizedError
from .parser import parse_update
from db.repository import TelegramRepository
from config import settings

logger = logging.getLogger(__name__)

class TelegramListener:
    def __init__(self, client: TelegramClient, repo: TelegramRepository):
        self.client = client
        self.repo = repo
        self.running = False
        self.fatal_error = False

    async def start(self):
        """Запуск цикла Long Polling."""
        self.running = True
        logger.info("Starting Telegram listener (Long Polling)...")
        
        try:
            await self.client.delete_webhook()
            logger.info("Webhook deleted. Using Long Polling.")
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            
        offset = await self.repo.get_offset()
        backoff = 1.0

        while self.running:
            try:
                updates = await self.client.get_updates(offset=offset, timeout=settings.poll_timeout)
                backoff = 1.0  # Reset on success
                
                if updates:
                    for update in updates:
                        parsed = parse_update(update)
                        if parsed:
                            await self.repo.upsert_chat(parsed.chat_id, parsed.chat_name)
                            await self.repo.save_message(
                                parsed.chat_id, parsed.message_id, parsed.sender_id,
                                parsed.sender_name, parsed.time, parsed.text, parsed.is_edit
                            )
                        offset = update["update_id"] + 1
                        
                    # Сохраняем offset после успешной обработки батча апдейтов
                    await self.repo.set_offset(offset)
                    
            except TelegramUnauthorizedError as e:
                logger.error(f"FATAL: Telegram API Error 401 (Unauthorized): {e}. Stopping listener.")
                self.fatal_error = True
                break
            except TelegramRateLimitError as e:
                logger.warning(f"Rate limited (429). Waiting for {e.retry_after}s.")
                await asyncio.sleep(e.retry_after)
            except TelegramAPIError as e:
                logger.error(f"Telegram API Error: {e}. Retrying in {backoff}s.")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)
            except asyncio.CancelledError:
                logger.info("Listener task cancelled.")
                raise
            except Exception as e:
                logger.exception(f"Unexpected error in listener: {e}. Retrying in {backoff}s.")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)
                
    def stop(self):
        """Сигнал на остановку слушателя."""
        self.running = False
