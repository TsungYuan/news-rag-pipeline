from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    top_k: int=5

class ChunkMetadata(BaseModel):
    news_id: int
    similarity: Optional[float] = None
    chunk_text: Optional[str] = None
    link: Optional[str] = None
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    query: str
    results: List[ChunkMetadata]

class Reference(BaseModel):
    news_id: Optional[int] = None
    title: Optional[str] = None
    publisher: Optional[str] = None

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
