from airflow.decorators import dag, task
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import pandas as pd
import re
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
import logging
import os
import json

logger = logging.getLogger(__name__)
DB_CONN = os.getenv("NEWS_DB_URL")

@dag(
    dag_id="rag_embedding_dag",
    start_date=datetime.now() - timedelta(days=1),
    schedule="*/10 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2}
)
def rag_embedding_pipline():

    create_chunk_embeddings_table = SQLExecuteQueryOperator(
        task_id='create_chunk_embeddings_table',
        conn_id='postgres_news_ai',
        sql="""
            CREATE TABLE IF NOT EXISTS news_chunk_embeddings (
            id SERIAL PRIMARY KEY,
            news_id INTEGER REFERENCES news_metadata(news_id),
            chunk_text TEXT,
            embedding vector(1024),
            metadata JSONB
            );
            """
    )

    @task()
    def fetch_unembedded_news():
        engine = create_engine(DB_CONN)
        query = """
            SELECT r.id AS news_id, r.content, m.title, m.published_at, m.publisher, m.category
            FROM news_raw_data r
            LEFT JOIN news_metadata m
            ON r.id = m.news_id
            WHERE r.id NOT IN (
                SELECT DISTINCT news_id 
                FROM news_chunk_embeddings
            )
            LIMIT 50;
        """
        df = pd.read_sql(query, engine)
        df["published_at"] = df["published_at"].astype(str)
        logger.info(f"{len(df)} news was fetched.")
        return df.to_dict(orient="records")
    
    @task()
    def chunk_text(news_list, max_length=300, overlap=50):
        chunked  = []
        current_chunk = ""

        for news in news_list:
            setences = re.split(r"[。！？]", news["content"])
            for sent in setences:
                if not sent.strip():
                    continue
                if len(current_chunk) + len(sent) <= max_length:
                    current_chunk += sent + "。"
                else:
                    if current_chunk:
                        chunk_idx = len(current_chunk)
                        chunked.append({
                            "news_id": news["news_id"],
                            "chunk_text": current_chunk,
                            "metadata": {
                                "news_id": news["news_id"],
                                "title": news["title"],
                                "published_at": news["published_at"],
                                "publisher": news["publisher"],
                                "category": news["category"],
                                "chunk_idx": chunk_idx
                            }
                        })
                    current_chunk = current_chunk[-overlap:] + sent if overlap > 0 else sent
            if  current_chunk:
                chunk_idx = len(current_chunk)
                chunked.append({
                    "news_id": news["news_id"],
                    "chunk_text": current_chunk,
                    "metadata": {
                        "news_id": news["news_id"],
                        "title": news["title"],
                        "published_at": news["published_at"],
                        "publisher": news["publisher"],
                        "category": news["category"],
                        "chunk_idx": chunk_idx
                    }
                })
        logger.info(f"{len(news_list)} news was splited into {len(chunked)} chunks.")
        return chunked
    
    @task(retries=3, retry_delay=timedelta(minutes=1))
    def generate_embedding(chunk_list):
        if not chunk_list:
            logger.info(f"No chunk data received. Skipping embedding generation.")
            return
    
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("BAAI/bge-m3")

        texts = [item["chunk_text"] for item in chunk_list]

        logger.info(f"Start generating embeddings for {len(chunk_list)} chunks.")
        dense_vec = model.encode(texts, convert_to_tensor=False)
        logger.info(f"{len(dense_vec)} of embeddings were generated.")

        result = []
        for i, vec in enumerate(dense_vec):
            result.append({
                "news_id": chunk_list[i]["news_id"],
                "chunk_text": chunk_list[i]["chunk_text"],
                "embedding": vec.tolist(),
                "metadata": chunk_list[i]["metadata"]
            })
        
        engine = create_engine(DB_CONN)
        df = pd.DataFrame(result)
        df["metadata"] = df["metadata"].apply(json.dumps)
        df.to_sql("news_chunk_embeddings", engine, if_exists="append", index=False)
        logger.info(f"Insert {len(df)} records to DB")

    
    t1 = create_chunk_embeddings_table
    raw_news = fetch_unembedded_news()
    chunked = chunk_text(raw_news)
    embedded = generate_embedding(chunked)

    t1 >> raw_news

rag_embedding_dag = rag_embedding_pipline()




