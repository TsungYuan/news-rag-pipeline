import re
import logging
import json

logger = logging.getLogger(__name__)

def chunk_article_content(news_list: list[dict], max_length: int = 300, overlap: int = 50) -> list[dict]:
    """
    Chunks the 'content' of news articles into smaller pieces with optional overlap.

    Args:
        news_list: A list of dictionaries, each containing news_id, content, title, etc.
        max_length: Maximum character length for each chunk.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        A list of dictionaries, each representing a text chunk with its metadata.
    """
    if not news_list:
        logger.info("No news articles provided for chunking.")
        return []

    chunked_data = []

    for news in news_list:
        news_id = news.get("news_id")
        content = news.get("content")
        
        # Prepare base metadata for all cases
        base_metadata = {
            "news_id": news_id,
            "title": news.get("title"),
            "published_at": news.get("published_at"),
            "publisher": news.get("publisher"),
            "category": news.get("category"),
            # chunk_idx will be added later for actual chunks
        }
        
        if not content:
            logger.warning(f"News ID {news_id} has no content. Creating an empty chunk entry to mark as processed.")
            # For news with no content, add a single placeholder chunk
            chunked_data.append({
                "news_id": news_id,
                "chunk_text": None,  # Explicitly set chunk_text to None
                "metadata": {**base_metadata, "chunk_idx": 0, "status": "no_content"} # Add status for easier tracking
            })
            continue

        sentences = re.split(r"[。！？]", content)
        current_chunk = ""
        chunk_counter = 0

        for sent_idx, sent in enumerate(sentences):
            sent = sent.strip()
            if not sent:
                continue

            if len(current_chunk) + len(sent) > max_length:
                if current_chunk:
                    chunked_data.append({
                        "news_id": news_id,
                        "chunk_text": current_chunk,
                        "metadata": {
                            **base_metadata,
                            "chunk_idx": chunk_counter
                        }
                    })
                    chunk_counter += 1
                current_chunk = current_chunk[-overlap:] + sent if overlap > 0 else sent
            else:
                current_chunk += sent + "。"

        # Add any remaining content as a final chunk
        if current_chunk:
            chunked_data.append({
                "news_id": news_id,
                "chunk_text": current_chunk,
                "metadata": {
                    **base_metadata,
                    "chunk_idx": chunk_counter
                }
            })

    logger.info(f"Chunked {len(news_list)} articles into {len(chunked_data)} chunks.")
    return chunked_data