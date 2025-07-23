from fastapi import APIRouter
from typing import Optional
from services.rag_agent import rag_ai_agent
from models.schemas import SearchRequest, RAGAgentResponse
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/rag_agent", response_model=RAGAgentResponse)
def rag_agent(request: SearchRequest):
    logger.info(f"Received search request: {request}")
    try: 
        return rag_ai_agent(request.query, request.top_k)
    except Exception as e:
        logger.exception("Error occurred during semantic search")
        raise e 