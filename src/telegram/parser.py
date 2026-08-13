import logging
from typing import Optional
from .models import ParsedMessage

logger = logging.getLogger(__name__)

def parse_update(update: dict) -> Optional[ParsedMessage]:
    update_id = update.get("update_id")
    if not update_id:
        return None
        
    is_edit = False
    msg_data = None
    
    if "message" in update:
        msg_data = update["message"]
    elif "edited_message" in update:
        msg_data = update["edited_message"]
        is_edit = True
    else:
        # Грациозно игнорируем channel_post, my_chat_member, callback_query и прочие
        return None
        
    text = msg_data.get("text") or msg_data.get("caption")
    if not text:
        # Игнорируем стикеры, медиа без caption, сервисные сообщения
        return None
        
    chat = msg_data.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return None
        
    chat_name = chat.get("title") or chat.get("username") or chat.get("first_name") or str(chat_id)
    
    sender = msg_data.get("from", {})
    sender_id = sender.get("id")
    sender_name = sender.get("username") or sender.get("first_name") or "Unknown"
    
    message_id = msg_data.get("message_id")
    # Date - оригинальное время (даже у edited_message, так как edit_date мы игнорируем)
    time = msg_data.get("date")
    
    if not message_id or not time:
        return None
        
    return ParsedMessage(
        update_id=update_id,
        message_id=message_id,
        chat_id=chat_id,
        chat_name=chat_name,
        sender_id=sender_id,
        sender_name=sender_name,
        time=time,
        text=text,
        is_edit=is_edit
    )
