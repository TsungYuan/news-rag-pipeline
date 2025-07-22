from fastapi import FastAPI
from routes import semantic_search, metadata_search
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World!"}

app.include_router(semantic_search.router)

app.include_router(metadata_search.router)