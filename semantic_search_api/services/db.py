from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)
DB_CNN_URL = os.getenv("NEWS_DB_URL")

engine = create_engine(DB_CNN_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_full_article_content(news_ids: List[int]) -> Dict[int, str]:
    if not news_ids:
        return{}
    
    placeholder = ",".join([str(nid) for nid in news_ids])
    sql = text(f"""
        SELECT id, content
        FROM news_raw_data
        WHERE id IN ({placeholder})
        ;
    """)

    full_contents = {}

    try: 
        with SessionLocal() as db:
            result = db.execute(sql).fetchall()
            for row in result:
                full_contents[row.id] = row.content
    except Exception as e:
        logger.error(f"Error fetching full article content for news_ids {news_ids}: {e}")
    return full_contents