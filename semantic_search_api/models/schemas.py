from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    top_k: int=5

class ChunkMetadata(BaseModel):
    news_id: int
    similarity: float
    content: str
    metadata: dict

class SearchResponse(BaseModel):
    query: str
    results: List[ChunkMetadata]

class Reference(BaseModel):
    title: str
    publisher: str

class Answer(BaseModel):
    summary: str
    references: List[Reference]

class RAGAgentResponse(BaseModel):
    query: str
    results: List[Any]
    answer: Answer
    
class MetadataSearchRequest(BaseModel):
    category: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    publisher: Optional[str] = None

class MetadataSearchResult(BaseModel):
    title: str
    publisher: str
    link: str

class MetadataSearchResponse(BaseModel):
    total_count: int
    results: List[MetadataSearchResult]
