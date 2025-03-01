################################################################################
# models.py
################################################################################
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    search_web: bool = False


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
