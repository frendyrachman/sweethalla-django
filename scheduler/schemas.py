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
    
class edit_schedule_payload(BaseModel):
    job_id: str
    scheduled_date: Optional[datetime] = None
    caption: Optional[str] = None

class edit_schedule_response(BaseModel):
    success: bool
    job_id: str
    scheduled_date: datetime
    caption: str