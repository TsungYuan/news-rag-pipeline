# 📰  News RAG Pipeline

A lightweight Retrieval-Augmented Generation (RAG) pipeline that allows users to query recent news, search semantically relevant content, and get natural language responses powered by Google Gemini.

## 🚀  Project Overview

This project builds an end-to-end pipeline combining ETL, vector search, and Large Language Models (LLMs) to summarize news articles based on a user's query.

### 🔧  Components

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

## 📦  Features

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

## ⚙️  Setup Instructions

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

## 📥  Example Usage

Enter a query like:

```
最近有什麼特別的社會新聞嗎？
```
The pipeline will:
1.	Search relevant news from the vector store
2.	Construct a prompt using top results
3.	Send the prompt to Gemini API
4.	Display the summary in the UI

## 🧠  Model Info

- **LLM**: gemini-2.5-pro via Google API

- **Embedding**: BAAI/bge-m3 (optimized for multilingual retrieval)

- **Vector DB**: PostgreSQL + pgvector 

- **ETL**: Airflow

## 🙌  Acknowledgements
- [Apache Airflow](https://airflow.apache.org/)
- [BAAI / bge-m3](https://huggingface.co/BAAI/bge-m3)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Gemini](https://ai.google.dev/)
- [Gradio](https://www.gradio.app/)
- [pgvector](https://github.com/pgvector/pgvector)





