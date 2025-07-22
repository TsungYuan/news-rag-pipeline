from airflow.decorators import dag, task
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import pandas as pd
import logging
import google.generativeai as genai
import os
import json
import time

logger = logging.getLogger(__name__)
DB_CONN = os.getenv("NEWS_DB_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CATEGORIES = ["政治", "經濟", "社會", "科技", "娛樂", "體育", "國際", "生活", "健康"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

BATCH_PROMPT_TEMPLATE = f"""
你是一位專業的新聞編輯，你的任務是根據以下提供的一系列新聞摘要，為每一則摘要分類。
請從以下類別中選擇一個：
[{', '.join(CATEGORIES)}]
你必須嚴格按照 JSON 格式回傳結果。回傳的結果應該是一個 JSON 陣列，陣列中的每個物件都包含 "id" 和 "category" 兩個鍵。
輸入: {{batch_of_summaries_in_json}}
"""

default_arg = {
    "retries": 2,
    "retry_delay": timedelta(minutes=1)
}

@dag(
    dag_id="insert_metadata",
    start_date=datetime.now() - timedelta(days=1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args=default_arg,
    tags=["news", "gemini", "metadata"]
)

def insert_metadata_pipeline():
    
    create_metadata_table = SQLExecuteQueryOperator(
        task_id='create_metadata_table',
        conn_id='postgres_news_ai',
        sql="""
            CREATE TABLE IF NOT EXISTS news_metadata (
                id SERIAL PRIMARY KEY,
                news_id INTEGER UNIQUE REFERENCES news_raw_data(id),
                title TEXT,
                published_at TIMESTAMP,
                publisher TEXT,
                category TEXT
            );
        """
    )

    @task()
    def fetch_unprocessed_news():
        engine = create_engine(DB_CONN)
        query = """
            SELECT id AS news_id, title, published_at, publisher, summary
            FROM news_raw_data
            WHERE id NOT IN (
                SELECT news_id
                FROM news_metadata
            )
            ORDER BY published_at DESC
            LIMIT 30;
        """
        df = pd.read_sql(query, engine)
        df["published_at"] = df["published_at"].astype(str)
        logger.info(f"{len(df)} of data was fetched.")
    
        return df.to_dict(orient="records")
    
    @task()
    def classify_news(news_list: list[dict]) -> list[dict]:
        if not news_list:
                logger.info(f"There is no news need to be classified.")
                return[]
            
        results = []
        BATCH_SIZE = 30

        for i in range(0, len(news_list), BATCH_SIZE):
            batch = news_list[i:i+BATCH_SIZE]
            summaries = []
            for item in batch:
                text_part = []
                if item.get("title"):
                    text_part.append(f"標題：{item['title']}")
                if item.get("summary"):
                    text_part.append(f"摘要：{item['summary']}")
                combined_text = "; ".join(text_part) or "無資料"
                summaries.append({
                    "id": item["news_id"], 
                    "summary": combined_text
                })

        summaries_json_string = json.dumps(summaries, ensure_ascii=False, indent=2)
        prompt = BATCH_PROMPT_TEMPLATE.format(batch_of_summaries_in_json=summaries_json_string)

        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            batch_result = json.loads(response.text)
            logging.info(f"{len(batch_result)} of news were classified.")
        except Exception as e:
            batch_result = [{"id": item["news_id"], "category": "API_Error"} for item in batch]

        results.extend(batch_result)
        time.sleep(1) 
        
        return results


    @task()
    def load_metadata(news_items: list[dict], classified_results: list):
        if not news_items or not classified_results:
            return "No data to insert."
        
        news_map = {item["news_id"]: item for item in news_items}
        engine = create_engine(DB_CONN)

        with engine.connect() as conn:
            for item in classified_results:
                try:
                    news = news_map.get(item["id"])
                    if not news:
                        continue
                    insert_stmt = text("""
                        INSERT INTO news_metadata (news_id, title, published_at, publisher, category)
                        VALUES (:news_id, :title, :published_at, :publisher, :category)
                        ON CONFLICT (news_id) DO NOTHING;
                    """)
                    conn.execute(insert_stmt, {
                        "news_id": news["news_id"],
                        "title": news["title"],
                        "published_at": news["published_at"],
                        "publisher": news["publisher"],
                        "category": item["category"]
                    })
                except Exception as e:
                    logger.warning(f"Insert failed for news_id={item['news_id']}: {e}")
            logger.info(f"{len(news_items)} of news were inserted.")


    t1 = create_metadata_table
    raw_news = fetch_unprocessed_news()
    classified_news = classify_news(raw_news)
    insert = load_metadata(raw_news, classified_news)

    t1 >> insert

insert_metadata = insert_metadata_pipeline()
