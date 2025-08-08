# api/models/message.py

# import types used by the models
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

# request body for POST /agent/send-message
class SendMessageInput(BaseModel):
    # optional: omit or null to start a new conversation
    conversation_id: Optional[str] = None
    # the user's message text
    content: str

    # example shown in Swagger
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": None,
                "content": "I feel spiritually dry lately."
            }
        }

# internal/db representation for messages saved in Mongo
class StoredMessage(BaseModel):
    # the conversation this message belongs to
    conversation_id: str
    # the user who sent/owns the message (filled server-side from JWT)
    user_id: str
    # who authored the message in the conversation flow
    role: Literal["system", "user"]
    # the message text (stored value)
    message: str
    # when the message was created (server-generated)
    created_at: datetime

    # example only for docs/dev reference
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "665f2a3b9c8e5b7a4d1f23ab",
                "user_id": "665f29f49c8e5b7a4d1f1ee1",
                "role": "user",
                "message": "I feel spiritually dry lately.",
                "created_at": "2025-08-07T16:45:00Z"
            }
        }
