from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ConversationCreate(BaseModel):
    user_id: str
    video_url: str
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True)

    id: str = Field(alias="_id")
    user_id: str
    video_url: str
    notes_url: Optional[str] = None
    concepts: List[str] = []
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
