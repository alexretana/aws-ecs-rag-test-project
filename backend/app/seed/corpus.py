import json
import os
import structlog

from app.rag.pipeline import RAGPipeline
from app.db.database import get_db, acquire_advisory_lock, release_advisory_lock

logger = structlog.get_logger()


def load_sample_documents() -> list:
    """Load sample documents from JSON file."""
    data_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "sample_documents.json"
    )
    
    with open(data_path, "r") as f:
        return json.load(f)


def seed_corpus(db_session) -> int:
    """Seed vector store with sample documents using advisory lock to prevent race conditions."""
    SEED_LOCK_ID = 1  # Fixed lock ID for seeding operation
    
    # Try to acquire advisory lock
    if not acquire_advisory_lock(db_session, SEED_LOCK_ID):
        logger.info("Seeding already in progress, skipping")
        return 0
    
    try:
        pipeline = RAGPipeline(db_session)
        documents = load_sample_documents()
        
        logger.info("Seeding corpus", document_count=len(documents))
        
        ingested_count = 0
        for doc in documents:
            try:
                document_id = pipeline.ingest_document(
                    content=doc["content"],
                    metadata={
                        "title": doc.get("title", ""),
                        **doc.get("metadata", {})
                    }
                )
                logger.info("Ingested document", title=doc.get("title"), document_id=document_id)
                ingested_count += 1
            except Exception as e:
                logger.error("Failed to ingest document", title=doc.get("title"), error=str(e))
        
        # Get final stats
        stats = pipeline.get_stats()
        logger.info("Seeding completed", 
                   ingested_count=ingested_count,
                   total_chunks=stats.get("total_chunks", 0))
        
        return ingested_count
        
    except Exception as e:
        logger.error("Seeding failed", error=str(e))
        return 0
    finally:
        # Always release the lock
        release_advisory_lock(db_session, SEED_LOCK_ID)


def seed_corpus_if_empty(db_session) -> int:
    """Seed corpus only if vector store is empty."""
    pipeline = RAGPipeline(db_session)
    stats = pipeline.get_stats()
    
    if stats.get("total_chunks", 0) == 0:
        logger.info("Vector store is empty, seeding sample documents")
        return seed_corpus(db_session)
    else:
        logger.info("Vector store already has data", chunks=stats.get("total_chunks", 0))
        return 0


def validate_documents() -> bool:
    """Validate sample documents format and content."""
    try:
        documents = load_sample_documents()
        
        required_fields = ["title", "content", "metadata"]
        for i, doc in enumerate(documents):
            for field in required_fields:
                if field not in doc:
                    logger.error("Document missing required field", index=i, field=field)
                    return False
                
                if not doc["content"] or not doc["content"].strip():
                    logger.error("Document has empty content", index=i, title=doc.get("title"))
                    return False
        
        logger.info("Document validation passed", count=len(documents))
        return True
        
    except Exception as e:
        logger.error("Document validation failed", error=str(e))
        return False


def get_seeding_stats(db_session) -> dict:
    """Get current seeding statistics."""
    pipeline = RAGPipeline(db_session)
    return pipeline.get_stats()