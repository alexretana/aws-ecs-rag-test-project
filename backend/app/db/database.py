import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from typing import Generator
import structlog

from app.config import get_settings

logger = structlog.get_logger()

# Global connection pool
pool: ConnectionPool = None


def get_database_url() -> str:
    """Construct database URL from settings."""
    settings = get_settings()
    return (
        f"postgresql://{settings.db_username}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )


def init_db():
    """Initialize database connection pool and create extensions."""
    global pool
    
    settings = get_settings()
    db_url = get_database_url()
    
    # Create connection pool with psycopg 3
    pool = ConnectionPool(
        conninfo=db_url,
        min_size=2,
        max_size=10,
        timeout=30,
        max_idle=300,
        kwargs={
            "row_factory": dict_row
        }
    )
    
    # Enable pgvector extension and create tables
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create document_chunks table with vector support
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    document_id VARCHAR NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(1536),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index on document_id for faster lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id 
                ON document_chunks(document_id)
            """)
            
            # Create vector index for similarity search
            # Note: ivfflat index requires at least 1000 rows to be effective
            # For small datasets, sequential scan may be faster
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
                ON document_chunks USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            
            conn.commit()
    
    logger.info("Database initialized successfully")


def get_db() -> Generator[psycopg.Connection, None, None]:
    """Get database connection from pool."""
    if pool is None:
        init_db()
    
    with pool.connection() as conn:
        yield conn


def acquire_advisory_lock(conn: psycopg.Connection, lock_id: int) -> bool:
    """
    Acquire a PostgreSQL advisory lock to prevent race conditions during seeding.
    Returns True if lock was acquired, False otherwise.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)", (lock_id,))
        result = cur.fetchone()
        return result['pg_try_advisory_lock'] if result else False


def release_advisory_lock(conn: psycopg.Connection, lock_id: int):
    """Release a PostgreSQL advisory lock."""
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_unlock(%s)", (lock_id,))


def close_db():
    """Close database connection pool."""
    global pool
    if pool:
        pool.close()
        logger.info("Database connection pool closed")