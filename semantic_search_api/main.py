import logging
from fastapi import FastAPI, HTTPException, Query, Depends
from routes import semantic_search, metadata_search, rag_agent
from datetime import date, datetime
from typing import Optional, List
from services.analytics_service import get_top_categories_from_db, get_top_publishers_from_db
from models.schemas import TopCategoriesResponse, TopPublishersResponse

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

app.include_router(rag_agent.router)

@app.get("/top_categories", response_model=TopCategoriesResponse)
async def get_top_categories_api(
    start_date: Optional[date] = Query(None, description="Start date for news articles (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for news articles (YYYY-MM-DD)"),
    limit: int = Query(5, ge=1, description="Number of top categories to return")
):
    """
    Retrieves the top N news categories within a specified date range.
    """
    try:
        top_categories, total_news_in_range = get_top_categories_from_db(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return TopCategoriesResponse(
            start_date=start_date,
            end_date=end_date,
            top_categories=top_categories,
            total_news_in_range=total_news_in_range
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top categories: {str(e)}")
    
@app.get("/top_publishers", response_model=TopPublishersResponse)
async def get_top_categories_api(
    start_date: Optional[date] = Query(None, description="Start date for news articles (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for news articles (YYYY-MM-DD)"),
    limit: int = Query(5, ge=1, description="Number of top categories to return")
):
    """
    Retrieves the top N news categories within a specified date range.
    """
    try:
        top_publishers, total_news_in_range = get_top_publishers_from_db(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return TopPublishersResponse(
            start_date=start_date,
            end_date=end_date,
            top_publishers=top_publishers,
            total_news_in_range=total_news_in_range
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top Publishers: {str(e)}")

