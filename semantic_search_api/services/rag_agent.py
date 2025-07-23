from services.llm import call_gemini, build_prompt
from services.search_top_K_chunks import semantic_search
from models.schemas import RAGAgentResponse
import logging

logger = logging.getLogger(__name__)

def rag_ai_agent(query: str, top_k: int = 5) -> RAGAgentResponse:
    logger.info(f"Start generate answers for query: {query}")
    try:
        search_response = semantic_search(query=query, top_k=top_k)
        results_dicts = [r.dict() for r in search_response.results]
        prompt = build_prompt(query, results_dicts)
        answer = call_gemini(prompt)

        return {
            "query": query,
            "results": results_dicts,
            "answer": answer
        }
    
    except Exception as e:
        logger.exception("Error in combined semantic_search_with_llm")
        return {
            "query": query,
            "results": [],
            "answer": f"Error: {str(e)}"
        }