from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SchedulePayload(BaseModel):
    platform: str
    media_type: str
    media_file_path: str
    schedule_time: datetime 
    caption: str


class AIEditPayload(BaseModel):
    media_file_path: str
    prompt: str