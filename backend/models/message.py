from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class MessageCreate(BaseModel):
    conversation_id: str
    user_id: str
    content: str
    message_type: str
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True)

    id: str = Field(alias="_id")
    conversation_id: str
    user_id: str
    content: str
    message_type: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
