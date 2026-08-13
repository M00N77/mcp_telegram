import pytest
from unittest.mock import AsyncMock
from src.services.telegram_service import TelegramService

@pytest.mark.asyncio
async def test_get_chat_info_group():
    # Arrange
    mock_repo = AsyncMock()
    mock_client = AsyncMock()
    mock_client.get_chat.return_value = {
        "type": "group",
        "title": "Dev Team",
        "description": "Team group"
    }
    mock_client.get_chat_member_count.return_value = 5
    
    service = TelegramService(mock_repo, mock_client)
    
    # Act
    result = await service.get_chat_info(-123456)
    
    # Assert
    assert "Тип: group" in result
    assert "Название: Dev Team" in result
    assert "Описание: Team group" in result
    assert "Участников: 5" in result
    mock_client.get_chat.assert_called_once_with(-123456)
    mock_client.get_chat_member_count.assert_called_once_with(-123456)

@pytest.mark.asyncio
async def test_get_chat_info_private():
    # Arrange
    mock_repo = AsyncMock()
    mock_client = AsyncMock()
    mock_client.get_chat.return_value = {
        "type": "private",
        "first_name": "Alice",
        "username": "alice123"
    }
    
    service = TelegramService(mock_repo, mock_client)
    
    # Act
    result = await service.get_chat_info(111)
    
    # Assert
    assert "Тип: private" in result
    assert "Название: Alice" in result
    assert "Username: @alice123" in result
    assert "Участников:" not in result
    mock_client.get_chat.assert_called_once_with(111)
    mock_client.get_chat_member_count.assert_not_called()
