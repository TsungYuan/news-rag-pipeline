from airflow.decorators import dag, task
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from src.db_utils import fetch_data_from_postgres
from src.gemini_classifier import GeminiNewsClassifier
import logging
import google.generativeai as genai
import os
import time

logger = logging.getLogger(__name__)
DB_CONN = os.getenv("NEWS_DB_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CATEGORIES = ["政治", "經濟", "社會", "科技", "娛樂", "體育", "國際", "生活", "健康"]

METADATA_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS news_metadata (
        id SERIAL PRIMARY KEY,
        news_id INTEGER UNIQUE REFERENCES news_raw_data(id),
        title TEXT,
        published_at TIMESTAMP,
        publisher TEXT,
        category TEXT
    );
"""

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")


@dag(
    dag_id="insert_metadata_pipeline", 
    start_date=datetime(2025, 7, 6), 
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
        "owner": "airflow"
    },
    tags=["news", "gemini", "metadata"]
)
def insert_metadata_pipeline():
    
    create_metadata_table_task = SQLExecuteQueryOperator(
        task_id='create_metadata_table_task',
        conn_id='postgres_news_ai',
        sql=METADATA_TABLE_SQL,
    )

    @task()
    def _fetch_unprocessed_news_callable(conn_id: str):
        query = f"""
            SELECT id AS news_id, title, published_at, publisher, summary
            FROM news_raw_data
            WHERE id NOT IN (
                SELECT news_id
                FROM news_metadata
            )
            ORDER BY published_at DESC
            LIMIT 30;
        """
        df = fetch_data_from_postgres(conn_id=conn_id, query=query)

        if not df.empty:
            df["published_at"] = df["published_at"].astype(str)
        logger.info(f"Fetched {len(df)} news for classification.")
        return df.to_dict(orient="records")
    
    @task()
    def _classify_news_callable(news_list: list[dict]):
        """
        Classifies news articles using Gemini and returns results.
        Initializes GeminiNewsClassifier within the task scope.
        """
        if not news_list:
            logger.info("No news received for classification.")
            return []

        classifier = GeminiNewsClassifier(api_key=GEMINI_API_KEY, categories=CATEGORIES)
        classified_results = classifier.classify_news_batch(news_list)

        time.sleep(1)

        return classified_results


    @task()
    def _load_metadata_callable(news_items: list[dict], classified_results: list):
        """
        Loads classified news metadata into the news_metadata table.
        """
        if not news_items or not classified_results:
            logger.info("No data to insert into news_metadata.")
            return

        news_map = {item["news_id"]: item for item in news_items}
        
        conn_id = "postgres_news_ai" 
        from src.db_utils import get_sql_alchemy_engine
        engine = get_sql_alchemy_engine(conn_id)
        
        inserted_count = 0
        with engine.connect() as conn:
            for classified_item in classified_results:
                news_id = classified_item["id"]
                category = classified_item["category"]
                news = news_map.get(news_id)

                if not news:
                    logger.warning(f"Original news data not found for classified news_id={news_id}. Skipping insertion.")
                    continue

                try:
                    insert_stmt = text("""
                        INSERT INTO news_metadata (news_id, title, published_at, publisher, category)
                        VALUES (:news_id, :title, :published_at, :publisher, :category)
                        ON CONFLICT (news_id) DO NOTHING;
                    """)
                    result = conn.execute(insert_stmt, {
                        "news_id": news["news_id"],
                        "title": news["title"],
                        "published_at": news["published_at"],
                        "publisher": news["publisher"],
                        "category": category
                    })
                    if result.rowcount > 0:
                        inserted_count += 1
                except Exception as e:
                    logger.warning(f"Insert/Update failed for news_id={news_id}: {e}")
            logger.info(f"Successfully processed and inserted/updated {inserted_count} records to news_metadata.")


    t_create_metadata_table = create_metadata_table_task
    t_raw_news = _fetch_unprocessed_news_callable(conn_id="postgres_news_ai")
    t_classified_news = _classify_news_callable(t_raw_news)
    t_insert_metadata = _load_metadata_callable(t_raw_news, t_classified_news)

    t_create_metadata_table >> t_raw_news
    t_raw_news >> t_classified_news
    t_classified_news >> t_insert_metadata

insert_metadata_dag = insert_metadata_pipeline()
