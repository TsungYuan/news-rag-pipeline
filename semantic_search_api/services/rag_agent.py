from services.llm import call_gemini, build_prompt
from services.search_top_K_chunks import semantic_search
from services.db import get_full_article_content
from models.schemas import RAGAgentResponse, Answer, ChunkMetadata
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def rag_ai_agent(query: str, top_k: int = 5) -> RAGAgentResponse:
    logger.info(f"RAG agent received query: {query}, top_k: {top_k}")

    try:
        search_response = semantic_search(query=query, top_k=top_k)
        retrieved_chunks_results_dicts: List[ChunkMetadata] = search_response.results 

        if not retrieved_chunks_results_dicts:
            logger.warning(f"No relevent chunks found for query: {query}")
            return RAGAgentResponse(
                query=query,
                results=[],
                answer=Answer(summary="根據目前的新聞內容，無法準確回答此問題。", references=[])
            )
        
        # if chunks doesn't provide enough information for LLM to process send the whole article of the news
        unique_news_ids = list(set([chunk.news_id for chunk in retrieved_chunks_results_dicts]))
        print(f"news ids: {unique_news_ids}")
        full_articles_content: Dict[int, str] = {}
        if len(unique_news_ids) <= 2: 
            full_articles_content = get_full_article_content(unique_news_ids)
            logger.info(f"Fetched {len(full_articles_content)} full articles for relevant news_ids.")
        else:
            logger.info(f"Skipping full article fetch: {len(unique_news_ids)} unique news IDs, more than 2.")

        llm_context_chunk = []
        for chunk in retrieved_chunks_results_dicts:
            current_full_article = full_articles_content.get(chunk.news_id, "")
            chunk_dict = {
                "news_id": chunk.news_id,
                "similarity": chunk.similarity,
                "chunk_text": chunk.chunk_text,
                "full_article": current_full_article,
                "meta_data": chunk.metadata
            }
            llm_context_chunk.append(chunk_dict)

        prompt = build_prompt(query, llm_context_chunk)
        logger.info("Calling Gemini LLM...")
        answer = call_gemini(prompt)
        logger.info("Gemini LLM call completed.")

        return {
            "query": query,
            "results": llm_context_chunk,
            "answer": answer
        }
    
    except Exception as e:
        logger.exception("Error in combined semantic_search_with_llm")
        return {
            "query": query,
            "results": [],
            "answer": f"Error: {str(e)}"
        }