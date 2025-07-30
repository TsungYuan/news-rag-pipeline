from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text
from datetime import date, datetime
from typing import List, Tuple, Dict, Optional
from services.db import SessionLocal
from models.schemas import CategoryCount, PublisherCount
import logging

logger = logging.getLogger(__name__)

def get_top_categories_from_db(start_date: Optional[date] = None, end_date: Optional[date] = None, limit: int = 5) -> Tuple[List[CategoryCount], int]:
    db = SessionLocal()
    try:
        actual_end_date = end_date if end_date is not None else date.today()
        
        where_clauses = []
        bind_params = {}

        if start_date:
            where_clauses.append("published_at >= :start_date")
            bind_params["start_date"] = datetime.combine(start_date, datetime.min.time())

        where_clauses.append("published_at <= :end_date")    
        bind_params["end_date"] = datetime.combine(actual_end_date, datetime.max.time())
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        logger.info(f"Where clauses: {where_sql}")

        total_count_sql = text(f"""
                SELECT COUNT(id) FROM news_metadata {where_sql};
            """)
        logger.info(f"Start quering total news count between {start_date} and {actual_end_date}.")
        total_news_in_range = db.execute(total_count_sql, bind_params).scalar_one()
        logger.info(f"Fetched {total_news_in_range} news.")

        top_categories_sql = text(f"""
                SELECT category, count(news_id) AS count
                FROM news_metadata
                {where_sql}
                GROUP BY category
                ORDER BY count DESC
                LIMIT :limit
                ;
            """)
        
        bind_params["limit"] = limit

        logger.info(f"Start fetching top {limit} categories.")
        category_counts_raw = db.execute(top_categories_sql, bind_params).fetchall()
        logger.info(f"Fetched.")

        top_categories = []
        for row in category_counts_raw:
            top_categories.append(CategoryCount(category=row.category, count=row.count))
        logger.debug(f"Top categories: {top_categories}, Total news count: {total_news_in_range}")

        return top_categories, total_news_in_range

    except Exception as e:
        print(f"Error fetching top categories from DB: {e}")
        raise


def get_top_publishers_from_db(start_date: Optional[date] = None, end_date: Optional[date] = None, limit: int = 5) -> Tuple[List[PublisherCount], int]:
    db = SessionLocal()
    try:
        actual_end_date = end_date if end_date is not None else date.today()
        where_clauses = []
        bind_params = {}

        if start_date:
            where_clauses.append("published_at >= :start_date")
            bind_params["start_date"] = datetime.combine(start_date, datetime.min.time())
        actual_end_date = end_date if end_date is not None else date.today()

        where_clauses.append("published_at <= :end_date")
        bind_params["end_date"] = datetime.combine(actual_end_date, datetime.max.time())
        logger.info(f"start date: {start_date}, end date: {actual_end_date}")
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        total_count_sql = text(f"""
                SELECT COUNT(id) FROM news_metadata {where_sql};
            """)
        logger.info(f"Start quering total news count between {start_date} and {actual_end_date}.")
        total_news_in_range = db.execute(total_count_sql, bind_params).scalar_one()
        logger.info(f"Fetched {total_news_in_range} news.")

        top_publishers_sql = text(f"""
                SELECT publisher, count(news_id) AS count
                FROM news_metadata
                {where_sql}
                GROUP BY publisher
                ORDER BY count DESC
                LIMIT :limit
                ;
            """)
        
        bind_params["limit"] = limit

        logger.info(f"Start fetching top {limit} publishers.")
        publisher_counts_raw = db.execute(top_publishers_sql, bind_params).fetchall()
        logger.info(f"Fetched.")

        top_publishers = []
        for row in publisher_counts_raw:
            top_publishers.append(PublisherCount(publisher=row.publisher, count=row.count))
        logger.debug(f"Top publishers: {top_publishers}, Total news count: {total_news_in_range}")

        return top_publishers, total_news_in_range

    except Exception as e:
        print(f"Error fetching top publishers from DB: {e}")
        raise