from sqlalchemy import create_engine, text
import os
import logging
import pandas as pd
import psycopg2 # Use psycopg2 directly if create_engine doesn't fully support pgvector registration

logger = logging.getLogger(__name__)

def get_sql_alchemy_engine(conn_id: str):
    """
    Creates and returns a SQLAlchemy engine using Airflow Connection.
    Note: Airflow's 'postgres_news_ai' conn_id provides the necessary URL.
    """
    db_url = os.getenv("NEWS_DB_URL") 
    if not db_url:
        logger.error("Database connection URL not found. Ensure NEWS_DB_URL is set.")
        raise ValueError("NEWS_DB_URL environment variable not set.")
    return create_engine(db_url)

def create_table_if_not_exists(conn_id: str, table_name: str, create_sql: str):
    """
    Executes SQL to create a table if it does not already exist.
    This function is primarily for SQL tasks managed by Airflow's SQLExecuteQueryOperator.
    However, for Python tasks needing to ensure a table exists, this can be used.
    """
    engine = get_sql_alchemy_engine(conn_id)
    with engine.connect() as conn:
        try:
            conn.execute(text(create_sql))
            conn.commit()
            logger.info(f"Table '{table_name}' ensured to exist.")
        except Exception as e:
            logger.error(f"Error creating table '{table_name}': {e}")
            conn.rollback()
            raise


def insert_dataframe_to_postgres(df: pd.DataFrame, table_name: str, conn_id: str, if_exists: str = "append", index: bool = False, unique_col: str = None):
    """
    Inserts DataFrame records into a PostgreSQL table, optionally checking for duplicates.
    """
    if df.empty:
        logger.info(f"No records to insert into '{table_name}'. DataFrame is empty.")
        return 0

    engine = get_sql_alchemy_engine(conn_id)
    records_inserted = 0

    try:
        with engine.connect() as conn:
            if unique_col:
                # Fetch existing unique identifiers to filter out duplicates
                existing_identifiers = pd.read_sql(f"SELECT {unique_col} FROM {table_name}", conn)
                df = df[~df[unique_col].isin(existing_identifiers[unique_col])]
                if df.empty:
                    logger.info(f"No new unique records to insert into '{table_name}'.")
                    return 0

            df.to_sql(table_name, conn, if_exists=if_exists, index=index)
            records_inserted = len(df)
            logger.info(f"Successfully inserted {records_inserted} records into '{table_name}'.")
            return records_inserted
    except Exception as e:
        logger.error(f"Error inserting records into '{table_name}': {e}")
        raise


def fetch_data_from_postgres(conn_id: str, query: str) -> pd.DataFrame:
    """
    Fetches data from PostgreSQL based on the given query and returns a DataFrame.
    """
    engine = get_sql_alchemy_engine(conn_id)
    try:
        df = pd.read_sql(query, engine)
        logger.info(f"Fetched {len(df)} records from database.")
        return df
    except Exception as e:
        logger.error(f"Error fetching data from PostgreSQL: {e}")
        raise


def update_records_in_postgres(conn_id: str, table_name: str, records: list[dict], unique_col: str, update_cols: list[str]):
    """
    Updates records in a PostgreSQL table.
    Assumes records is a list of dicts, each containing unique_col and update_cols.
    """
    engine = get_sql_alchemy_engine(conn_id)
    conn = None
    try:
        conn = engine.connect()
        # Begin transaction for batch update
        trans = conn.begin()
        updated_count = 0
        for record in records:
            set_clauses = [f"{col} = :{col}" for col in update_cols]
            set_clause_str = ", ".join(set_clauses)
            stmt = text(f"""
                UPDATE {table_name}
                SET {set_clause_str}
                WHERE {unique_col} = :{unique_col};
            """)
            result = conn.execute(stmt, record)
            updated_count += result.rowcount
        trans.commit()
        logger.info(f"Successfully updated {updated_count} records in '{table_name}'.")
    except Exception as e:
        logger.error(f"Error updating records in '{table_name}': {e}")
        if conn:
            trans.rollback()
        raise
    finally:
        if conn:
            conn.close()
