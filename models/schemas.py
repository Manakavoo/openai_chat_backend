# models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class MessageHistory(BaseModel):
    role: str
    content: str

class VideoContext(BaseModel):
    id: str
    title: str
    description: Optional[str] = None

class OpenAIRequest(BaseModel):
    message: str
    history: List[MessageHistory] = []
    videoContext: Optional[VideoContext] = None
    timestamp: Optional[str] = None

class OpenAIResponse(BaseModel):
    response: str
    conversationId: str

class ConversationInfo(BaseModel):
    id: str
    title: str
    updatedAt: datetime

class TutorRequest(BaseModel):
    message: str
    history: List[MessageHistory] = []

class TutorResponse(BaseModel):
    response: str
    conversationId: str