from services.embedder import embed_text
from services.db import SessionLocal
from models.schemas import ChunkMetadata, SearchResponse
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def semantic_search(query: str, top_k: int=5) -> SearchResponse:
    logger.info(f"Starting semantic search with query: {query}, top_k: {top_k}")

    try: 
        embedding_query = embed_text(query)

        with SessionLocal() as db:
            sql = text("""
                    WITH similarity_search AS (
                       SELECT DISTINCT ON (news_id)
                            news_id, metadata, 
                            1 - (embedding <=> CAST(:embedding_query AS vector)) AS similarity
                       FROM news_chunk_embeddings
                       ORDER BY news_id, similarity DESC
                    ),
                    top_k_news AS (
                       SELECT *
                       FROM similarity_search
                       ORDER BY similarity DESC
                       LIMIT :top_k
                    )
                    SELECT tk.news_id, tk.metadata, tk.similarity, nr.content
                    FROM top_k_news tk
                    JOIN news_raw_data nr
                       ON nr.id = tk.news_id
                    ORDER BY tk.similarity DESC
                    ;
            """)

            similarity_result = db.execute(sql, {
                "query": query,
                "embedding_query": embedding_query,
                "top_k": top_k
            }).fetchall()

            logger.info(f"Retrieved {len(similarity_result)} results from DB")

            results = [
                ChunkMetadata(
                    news_id=row.news_id,
                    metadata=row.metadata,
                    content=row.content,
                    similarity=row.similarity
                )
                for row in similarity_result
            ]
            logger.debug(f"Results: {results}")
            return SearchResponse(query=query, results=results)
    
    except Exception as e:
        logger.exception("Error occurred in semantic_search")
        raise


        