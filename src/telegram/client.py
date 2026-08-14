import httpx
import logging
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class TelegramAPIError(Exception):
    """Base exception for Telegram API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class TelegramRateLimitError(TelegramAPIError):
    """Exception raised for 429 Too Many Requests."""

    def __init__(self, message: str, retry_after: int):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class TelegramUnauthorizedError(TelegramAPIError):
    """Exception raised for 401 Unauthorized (invalid/revoked token)."""

    def __init__(self, message: str = "Invalid or revoked bot token"):
        super().__init__(message, status_code=401)


class TelegramForbiddenError(TelegramAPIError):
    """Exception raised for 403 Forbidden (bot blocked/no access)."""

    def __init__(self, message: str = "Bot blocked or no access to chat", description: str = ""):
        super().__init__(message, status_code=403)
        self.description = description


class TelegramBadRequestError(TelegramAPIError):
    """Exception raised for 400 Bad Request (e.g., chat not found)."""

    def __init__(self, message: str, description: str):
        super().__init__(message, status_code=400)
        self.description = description


class TelegramClient:
    def __init__(self, token: str):
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.client: Optional[httpx.AsyncClient] = None

    async def start(self):
        """Initializes the HTTP client."""
        if not self.client:
            # timeout=60.0 allows enough time for long polling (default 25-30s)
            self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
            logger.info("Telegram HTTP client started.")

    async def close(self):
        """Closes the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("Telegram HTTP client closed.")

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Base request method with error handling."""
        if not self.client:
            raise RuntimeError("TelegramClient is not initialized. Call start() first.")

        try:
            response = await self.client.request(method, endpoint, **kwargs)
        except httpx.RequestError as e:
            logger.error(f"Network error while connecting to Telegram: {e}")
            raise TelegramAPIError(f"Network error: {e}")

        # Handling 429 Too Many Requests
        if response.status_code == 429:
            try:
                data = response.json()
            except Exception:
                raise TelegramAPIError(f"HTTP Error {response.status_code} (Non-JSON response)")
            retry_after = data.get("parameters", {}).get("retry_after", 5)
            logger.warning(f"Rate limited (429). Retry after {retry_after}s.")
            raise TelegramRateLimitError("Rate limit exceeded", retry_after=retry_after)

        # Handling structured errors 400 and 403 (and 401/404)
        if response.status_code in (400, 401, 403, 404):
            try:
                data = response.json()
            except Exception:
                raise TelegramAPIError(f"HTTP Error {response.status_code} (Non-JSON response)")
            
            description = data.get("description", "Unknown error")
            logger.error(f"Telegram API Error {response.status_code}: {description}")
            
            if response.status_code == 403:
                raise TelegramForbiddenError(f"API Error 403: {description}", description=description)
            elif response.status_code == 400:
                raise TelegramBadRequestError(f"API Error 400: {description}", description=description)
            elif response.status_code == 404:
                raise TelegramBadRequestError(f"API Error 404: {description}", description=description)
            elif response.status_code == 401:
                raise TelegramUnauthorizedError()

        # Handling any other unexpected status code
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
            raise TelegramAPIError(
                f"HTTP Error {e.response.status_code}",
                status_code=e.response.status_code,
            )

        # Parse JSON and verify 'ok'
        data = response.json()
        if not data.get("ok"):
            description = data.get("description", "Unknown error")
            raise TelegramAPIError(
                f"Telegram returned ok=false: {description}", response_data=data
            )

        return data.get("result")

    async def get_me(self) -> Dict[str, Any]:
        """Calls getMe to verify token and bot info."""
        return await self._request("GET", "getMe")

    async def delete_webhook(self) -> bool:
        """Calls deleteWebhook to ensure single-bot long polling is allowed."""
        return await self._request("POST", "deleteWebhook")

    async def get_updates(
        self, offset: Optional[int] = None, timeout: int = 25
    ) -> list:
        """Calls getUpdates for long polling."""
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        return await self._request("GET", "getUpdates", params=params)

    async def send_message(self, chat_id: int, text: str) -> Dict[str, Any]:
        """Calls sendMessage to post text to a specific chat."""
        payload = {"chat_id": chat_id, "text": text}
        return await self._request("POST", "sendMessage", json=payload)

    async def get_chat(self, chat_id: int) -> Dict[str, Any]:
        """Calls getChat to get detailed information about a chat."""
        payload = {"chat_id": chat_id}
        return await self._request("POST", "getChat", json=payload)

    async def get_chat_member_count(self, chat_id: int) -> int:
        """Calls getChatMemberCount to get the number of members in a chat."""
        payload = {"chat_id": chat_id}
        return await self._request("POST", "getChatMemberCount", json=payload)


if __name__ == "__main__":
    # Временный тестовый скрипт для локальной проверки
    import os
    import sys

    # Добавляем корень проекта в пути
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import settings
    from utils.logging import setup_logging

    async def run_test():
        setup_logging()
        client = TelegramClient(settings.telegram_bot_token)
        await client.start()
        try:
            logger.info("Testing get_me()...")
            me = await client.get_me()
            logger.info(f"Bot info: {me}")

            logger.info("Calling deleteWebhook...")
            await client.delete_webhook()

            logger.info(
                "Polling getUpdates for 5 seconds (send a message to the bot now!)..."
            )
            updates = await client.get_updates(timeout=5)
            logger.info(f"Received updates: {updates}")
        except Exception as e:
            logger.error(f"Test failed: {e}")
        finally:
            await client.close()

    asyncio.run(run_test())
