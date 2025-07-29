from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime, date

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

class CategoryCount(BaseModel):
    category: str
    count: int

class TopCategoriesResponse(BaseModel):
    start_date: Optional[date] = Field(None, description="start analyze from (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="stop analyze at (YYYY-MM-DD)")
    top_categories: List[CategoryCount] = Field(default_factory=list, description="count top n category news")
    total_news_in_range: int = Field(0, description="total news count within the time period")

class PublisherCount(BaseModel):
    publisher: str
    count: int

class TopPublishersResponse(BaseModel):
    start_date: Optional[date] = Field(None, description="start analyze from (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="stop analyze at (YYYY-MM-DD)")
    top_publishers: List[PublisherCount] = Field(default_factory=list, description="count top n publisher")
    total_news_in_range: int = Field(0, description="total news count within the time period")
