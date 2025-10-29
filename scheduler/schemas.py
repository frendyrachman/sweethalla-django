from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UploadPostSchedulePayload(BaseModel):
    user: str = 'karenbot'
    platform: list[str]
    video: Optional[str]
    photos: Optional[list[str]]
    title: str
    scheduled_date: datetime 


class AIEditPayload(BaseModel):
    media_file_path: str
    prompt: str
    
class AIEditResponse(BaseModel):
    edited_media_file_path: str

class AICaptionPayload(BaseModel):
    media_file_path: str

class AICaptionResponse(BaseModel):
    caption: str