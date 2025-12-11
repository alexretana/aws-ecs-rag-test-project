from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Document(BaseModel):
    """Document model for RAG corpus."""
    id: Optional[str] = None
    content: str
    metadata: dict = {}
    created_at: Optional[datetime] = None


class QueryRequest(BaseModel):
    """Query request model."""
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    """Query response model."""
    answer: str
    sources: List[dict]
    query: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class DocumentChunk(BaseModel):
    """Chunk of a document with embedding."""
    id: Optional[str] = None
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: dict = {}