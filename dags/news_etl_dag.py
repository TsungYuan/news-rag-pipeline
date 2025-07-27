import pandas as pd
import logging
from airflow import DAG 
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from flask import jsonify
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from src.news_extractor import fetch_yahoo_news_articles
from src.db_utils import insert_dataframe_to_postgres

logger = logging.getLogger("airflow.task")

NEWS_RAW_DATA_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS news_raw_data (
        id SERIAL PRIMARY KEY,
        title TEXT,
        link TEXT, -- Added UNIQUE constraint for link
        published_at TIMESTAMP,
        summary TEXT,
        publisher TEXT,
        content TEXT
    );
"""

def _extract_news_callable(**context):
    """Airflow callable to extract news and push to XCom."""
    news_items = fetch_yahoo_news_articles()
    context["ti"].xcom_push(key="extracted_news_items", value=news_items)
    logger.info(f"Pushed {len(news_items)} extracted news items to XCom.")

def _load_news_callable(**context):
    """Airflow callable to load news from XCom to PostgreSQL."""
    records = context["ti"].xcom_pull(task_ids="extract_news_task", key="extracted_news_items")
    if not records:
        logger.info("No news records to load.")
        return

    df = pd.DataFrame(records)
    inserted_count = insert_dataframe_to_postgres(
        df=df,
        table_name="news_raw_data",
        conn_id="postgres_news_ai",
        unique_col="link"
    )
    logger.info(f"Finished loading news. {inserted_count} new records were inserted.")


with DAG(
    dag_id="news_etl_pipeline", 
    start_date=datetime(2025, 7, 6),
    schedule="*/20 * * * *", 
    max_active_runs=1,
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "owner": "David" 
    },
    catchup=False,
    tags=["news", "etl", "raw_data"]
) as dag:
    create_news_raw_data_table = SQLExecuteQueryOperator(
        task_id='create_news_raw_data_table',
        conn_id='postgres_news_ai',
        sql=NEWS_RAW_DATA_TABLE_SQL,
    )

    extract_news_task = PythonOperator(
        task_id='extract_news_task',
        python_callable=_extract_news_callable,
    )

    load_news_task = PythonOperator(
        task_id='load_news_task', 
        python_callable=_load_news_callable,
    )

    trigger_insert_metadata_dag = TriggerDagRunOperator(
        task_id="trigger_insert_metadata_dag", 
        trigger_dag_id="insert_metadata_pipeline",
        wait_for_completion=False, 
    )

    create_news_raw_data_table >> extract_news_task >> load_news_task >> trigger_insert_metadata_dag










