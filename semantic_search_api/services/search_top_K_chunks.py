from services.embeddor import embed_text
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
            sql_only_chunk = text("""
                    SELECT ce.news_id, ce.chunk_text, ce.metadata, rd.link,
                        1 - (ce.embedding <=> CAST(:embedding_query AS vector)) AS similarity
                    FROM news_chunk_embeddings ce
                    LEFT JOIN news_raw_data rd
                        ON ce.news_id = rd.id
                    WHERE embedding IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT :top_k;
                    ;
            """)

            similarity_result = db.execute(sql_only_chunk, {
                "query": query,
                "embedding_query": embedding_query,
                "top_k": top_k
            }).fetchall()

            logger.info(f"Retrieved {len(similarity_result)} results from DB")

            results = [
                ChunkMetadata(
                    news_id=row.news_id,
                    metadata=row.metadata,
                    chunk_text=row.chunk_text,
                    similarity=row.similarity,
                    link=row.link
                )
                for row in similarity_result
            ]
            logger.debug(f"Results: {results}")
            return SearchResponse(query=query, results=results)
    
    except Exception as e:
        logger.exception("Error occurred in semantic_search")
        raise


        