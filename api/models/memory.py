# models/memory.py
from pydantic import BaseModel
from typing import Optional

class Memory(BaseModel):
    user_id: str
    memory: str
