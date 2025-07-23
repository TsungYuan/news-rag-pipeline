# 📰 &nbsp;News RAG Pipeline

A lightweight Retrieval-Augmented Generation (RAG) pipeline that allows users to query recent news, search semantically relevant content, and get natural language responses powered by Google Gemini.

## 🚀 &nbsp;Project Overview

This project builds an end-to-end pipeline combining ETL, vector search, and Large Language Models (LLMs) to summarize news articles based on a user's query.

### 🔧 &nbsp;Components

| Component        | Tool/Tech                         |
|----------------|:---------------------------------:|
| ETL Pipeline     | Apache Airflow                    |
| Embedding Model  | `BAAI/bge-m3` via SentenceTransformer |
| Vector Database  | PostgreSQL with `pgvector` extension |
| LLM              | Google Gemini Pro 2.5 (via API)   |
| Backend API      | FastAPI                          |
| Frontend         | Gradio                           |
| Language         | Python 3.10+                     |
| Dependency Mgmt  | `requirements.txt`               |

---

## 📦 &nbsp;Features

- **Automated ETL with Airflow**  
  Periodically crawls and stores the latest news content from sources.

- **Embedding & Vector Search**  
  Converts text into dense vectors using `BAAI/bge-m3` and stores them in PostgreSQL using `pgvector`.

- **RAG with Gemini API**  
  Uses Gemini 2.5 Pro to generate natural language answers based on top-k similar articles.

- **API & UI**  
  - FastAPI serves the backend logic.  
  - Gradio provides a simple web interface for interaction.

---

## ⚙️ &nbsp;Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/news-rag-pipeline.git
cd news-rag-pipeline
```

### 2. Install Dependencies

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

###  3. Environment Variables

Create a .env file and add your Gemini API key:

```env
AIRFLOW_UID={AIRFLOW_UID}
NEWS_DB_URL={postges url}
GEMINI_API_KEY={GEMINI_API_KEY}
```

### 4. Run ETL (via Airflow)

Make sure Airflow is configured properly to run the DAGs that fetch and embed news.

```bash
# Start Airflow scheduler and webserver
airflow scheduler
airflow webserver
```

### 5. Run Backend

Make sure Airflow is configured properly to run the DAGs that fetch and embed news.

```bash
uvicorn app.main:app --reload
```

### 6. Launch Gradio UI

Make sure Airflow is configured properly to run the DAGs that fetch and embed news.

```bash
python gradio_app.py
```

## 📥 &nbsp;Example Usage

Enter a query like:

```
最近有什麼特別的社會新聞嗎？
```
The pipeline will:
1.	Search relevant news from the vector store
2.	Construct a prompt using top results
3.	Send the prompt to Gemini API
4.	Display the summary in the UI

Output will be like:

answer:
```
{
    "summary":
    "近期社會新聞事件涵蓋多個面向。其中，網紅「仙塔律師」李宜諪因涉嫌洩密給靈骨塔詐騙集團，遭檢方調查後以70萬元交保，她事後發文澄清外界對其私生活與財務狀況的傳聞。在教育方面，為應對青少年網路成癮與隱私外洩風險，國立台灣師範大學在花蓮富里國中舉辦媒體素養營，引導學生建立健康的網路使用習慣。此外，新北市客家義民爺文化祭也展開暖身活動，推出「鶯歌燒彩繪陶豬」比賽，以具環保意識與創意的方式延續傳統信仰。"
    "references":[
        {
            "title": "...",
            "publisher": "..."
        },
        {
            "title": "...",
            "publisher": "..."
        },
        ...
    ]

}
```

result:
```
[
    {
        "news_id": 1,
        "similarity": 0.5624959953117447,
        "content": "...",
        "metadata": {
            "news_id": 1,
            "title": "...",
            "category": "社會",
            "chunk_idx": 200,
            "publisher": "...",
            "pubished_at": "date time"
        }

    },
    ...
]
```

## 🧠 &nbsp;Model Info

- **LLM**: gemini-2.5-pro via Google API

- **Embedding**: BAAI/bge-m3 (optimized for multilingual retrieval)

- **Vector DB**: PostgreSQL + pgvector 

- **ETL**: Airflow

## 🙌 &nbsp;Acknowledgements
- [Apache Airflow](https://airflow.apache.org/)
- [BAAI / bge-m3](https://huggingface.co/BAAI/bge-m3)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Gemini](https://ai.google.dev/)
- [Gradio](https://www.gradio.app/)
- [pgvector](https://github.com/pgvector/pgvector)





