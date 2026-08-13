from pydantic import BaseModel
from typing import Optional

class ParsedMessage(BaseModel):
    update_id: int
    message_id: int
    chat_id: int
    chat_name: str
    sender_id: Optional[int]
    sender_name: Optional[str]
    time: int
    text: str
    is_edit: bool
