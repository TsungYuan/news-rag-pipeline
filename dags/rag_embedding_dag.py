from airflow.decorators import dag, task
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from src.db_utils import fetch_data_from_postgres
from src.text_processor import chunk_article_content
from src.embedding_generator import generate_embeddings_for_chunks
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
import logging

logger = logging.getLogger(__name__)

CHUNK_EMBEDDINGS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS news_chunk_embeddings (
        id SERIAL PRIMARY KEY,
        news_id INTEGER REFERENCES news_metadata(news_id),
        chunk_text TEXT,
        embedding vector(1024), -- Ensure this matches your model's embedding dimension
        metadata JSONB
    );
"""
embedding_model_name = "BAAI/bge-m3"


@dag(
    dag_id="rag_embedding_pipeline",
    start_date=datetime(2025, 7, 6),
    schedule="*/10 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
        "owner": "airflow"
    },
    tags=["rag", "embedding", "news"]
)
def rag_embedding_pipeline():

    create_chunk_embeddings_table = SQLExecuteQueryOperator(
        task_id='create_chunk_embeddings_table',
        conn_id='postgres_news_ai',
        sql=CHUNK_EMBEDDINGS_TABLE_SQL,
    )

    @task()
    def _fetch_unembedded_news_callable(conn_id: str):
        """
        Fetches news articles that have not yet been chunked and embedded.
        """
        query = f"""
            SELECT r.id AS news_id, r.content, m.title, m.published_at, m.publisher, m.category
            FROM news_raw_data r
            LEFT JOIN news_metadata m
            ON r.id = m.news_id
            WHERE r.id NOT IN (
                SELECT DISTINCT news_id 
                FROM news_chunk_embeddings
            )
            LIMIT 50
            ;
        """
        df = fetch_data_from_postgres(conn_id=conn_id, query=query)
        if not df.empty:
            df["published_at"] = df["published_at"].astype(str)
        logger.info(f"Fetched {len(df)} news for chunking and embedding.")
        return df.to_dict(orient="records")

    @task()
    def _chunk_text_callable(news_list: list[dict]):
        """
        Chunks the text content of news articles.
        Retrieves chunking parameters from Airflow Variables.
        """
        if not news_list:
            logger.info("No news received for chunking.")
            return []

        chunked_data = chunk_article_content(news_list)
        return chunked_data

    @task(retries=3, retry_delay=timedelta(minutes=1))
    def _generate_embedding_callable(chunk_list: list[dict], conn_id: str):
        """
        Generates embeddings for text chunks and loads them into the database.
        Retrieves model name from Airflow Variable.
        """
        if not chunk_list:
            logger.info("No chunks to embed.")
            return

        inserted_count = generate_embeddings_for_chunks(
            chunk_list=chunk_list,
            model_name=embedding_model_name,
            conn_id=conn_id
        )
        logger.info(f"Total {inserted_count} chunk embeddings processed.")

    t_create_chunk_embeddings_table = create_chunk_embeddings_table
    t_fetch_unembedded_news = _fetch_unembedded_news_callable(conn_id="postgres_news_ai")
    t_chunked_news = _chunk_text_callable(t_fetch_unembedded_news)
    t_generate_embedding = _generate_embedding_callable(t_chunked_news, conn_id="postgres_news_ai")

    t_create_chunk_embeddings_table >> t_fetch_unembedded_news
    t_fetch_unembedded_news >> t_chunked_news
    t_chunked_news >> t_generate_embedding

rag_embedding_dag = rag_embedding_pipeline()




