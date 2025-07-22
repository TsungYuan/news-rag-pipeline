from airflow import DAG 
from datetime import datetime, timedelta
import feedparser
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
import os
from flask import jsonify
import logging
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

logger = logging.getLogger("airflow.task")

def fetch_yahoo_news_to_google_sheet():
    try: 
        rss_url = "https://tw.news.yahoo.com/rss"

        feed = feedparser.parse(rss_url)
        news_items = []

        for entry in feed.entries:
            url = entry.link
            try:
                req = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(req.text, "html.parser")

                article = soup.find("div", class_="caas-body")
                paragraphs = article.find_all("p") if article else []
                full_text =  "".join(p.text for p in paragraphs)

                source_tag = soup.find("span", class_="caas-attr-provider")
                source = source_tag.text.strip() if source_tag else "Unknown"
                
                news_items.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published_at': entry.published,
                    'summary': entry.summary,
                    'publisher': source,
                    'content': full_text
                })
            except Exception as e:
                logger.info(f"Error fetching {url}: {e}")

        return news_items
    
    except Exception as e:
        logger.info(f"Error: {str(e)}")

def save_to_postgres(**context):
    records = context["ti"].xcom_pull(task_ids="extract_news")
    df = pd.DataFrame(records)

    engine = create_engine("postgresql+psycopg2://airflow:airflow@postgres:5432/news_ai")
    with engine.connect() as conn:
        existing_links = pd.read_sql("SELECT link FROM news_raw_data", conn)

    if not existing_links.empty:
        df = df[~df["link"].isin(existing_links["link"])]
    if not df.empty:
        df.to_sql("news_raw_data", engine, if_exists="append", index=False)
        logger.info(f"Insert {len(df)} records to DB")
    else:
        logger.info(f"No new records to insert.")

with DAG(
    dag_id="news_etl",
    start_date=datetime(2025, 7, 6),
    schedule="*/20 * * * *",
    max_active_runs=1,
        default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=5)
    }
) as dag:
    create_table = SQLExecuteQueryOperator(
        task_id = 'create_news_raw_data_table',
        conn_id = 'postgres_news_ai',
        sql= """
            CREATE TABLE IF NOT EXISTS news_raw_data (
                id SERIAL PRIMARY KEY,
                title TEXT,
                link TEXT,
                published_at TIMESTAMP,
                summary TEXT,
                publisher TEXT,
                content TEXT
            );
            """,
    )

    extract = PythonOperator(
        task_id = 'extract_news',
        python_callable=fetch_yahoo_news_to_google_sheet
    )

    load = PythonOperator(
        task_id = 'load_news',
        python_callable = save_to_postgres
    )

    trigger_dag_insert_metadata = TriggerDagRunOperator(
        task_id="trigger_dag_insert_metadata",
        trigger_dag_id="insert_metadata",
        wait_for_completion=False
    )

    create_table >> extract >> load >> trigger_dag_insert_metadata










