# models/conversation.py
from pydantic import BaseModel
from typing import Optional

class Conversation(BaseModel):
    id: str
    user_id: str
    topic: Optional[str] = "Untitled"
