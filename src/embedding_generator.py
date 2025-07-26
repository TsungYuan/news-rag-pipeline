from sentence_transformers import SentenceTransformer
import logging
import pandas as pd
import json
import numpy as np # Ensure numpy is imported for array operations

logger = logging.getLogger(__name__)

_embedding_model = None

def get_sentence_transformer_model(model_name: str) -> SentenceTransformer:
    """
    Loads and caches the SentenceTransformer model.
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading SentenceTransformer model: {model_name}...")
        try:
            _embedding_model = SentenceTransformer(model_name)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model {model_name}: {e}")
            raise
    return _embedding_model

def generate_embeddings_for_chunks(chunk_list: list[dict], model_name: str, conn_id: str) -> int:
    """
    Generates embeddings for a list of text chunks and saves them to the database.
    Handles chunks with None content by assigning None to embedding.

    Args:
        chunk_list: A list of dictionaries, each with 'chunk_text', 'news_id', 'metadata'.
        model_name: The name of the SentenceTransformer model to use.
        conn_id: The Airflow connection ID for PostgreSQL.

    Returns:
        The number of records successfully inserted.
    """
    if not chunk_list:
        logger.info("No chunk data received. Skipping embedding generation.")
        return 0

    model = get_sentence_transformer_model(model_name)
    
    records_to_insert = []
    
    # Process each chunk individually to handle None content gracefully
    for item in chunk_list:
        news_id = item["news_id"]
        chunk_text = item["chunk_text"]
        metadata = item["metadata"]
        
        embedding_vec = None # Initialize embedding as None
        
        if chunk_text is not None and len(chunk_text.strip()) > 0:
            try:
                # Encode only if chunk_text is valid
                embedding_vec = model.encode(chunk_text, normalize_embeddings=True, convert_to_tensor=False).tolist()
                logger.debug(f"Generated embedding for news_id: {news_id}, chunk_idx: {metadata.get('chunk_idx')}")
            except Exception as e:
                logger.warning(f"Failed to generate embedding for news_id {news_id}, chunk_idx {metadata.get('chunk_idx')}: {e}. Storing None embedding.")
        else:
            logger.info(f"Chunk text is empty or None for news_id: {news_id}, chunk_idx: {metadata.get('chunk_idx')}. Storing None embedding.")

        records_to_insert.append({
            "news_id": news_id,
            "chunk_text": chunk_text, # Will be None for no-content news
            "embedding": embedding_vec, # Will be None for no-content or failed embedding
            "metadata": json.dumps(metadata, ensure_ascii=False)
        })

    if not records_to_insert:
        logger.info("No valid records to insert after embedding generation.")
        return 0

    df = pd.DataFrame(records_to_insert)

    from src.db_utils import insert_dataframe_to_postgres
    inserted_count = insert_dataframe_to_postgres(
        df=df,
        table_name="news_chunk_embeddings",
        conn_id=conn_id,
        if_exists="append", # Assuming you want to append new chunks
        index=False # Don't write DataFrame index as a column
    )
    return inserted_count