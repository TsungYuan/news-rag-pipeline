from fastapi import APIRouter
from services.search_top_K_chunks import semantic_search
from models.schemas import SearchRequest, SearchResponse
import logging

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@router.post("/semantic_search", response_model=SearchResponse)
def search_news(request: SearchRequest):
    logger.info(f"Received search request: {request}")
    try: 
        return semantic_search(request.query, request.top_k)
    except Exception as e:
        logger.exception("Error occurred during semantic search")
        raise e 