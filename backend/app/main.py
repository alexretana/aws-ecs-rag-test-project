import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import structlog

# X-Ray instrumentation
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

from app.config import get_settings
from app.models import QueryRequest, QueryResponse, HealthResponse
from app.db.database import get_db, init_db
from app.db.vector_store import VectorStore
from app.rag.pipeline import RAGPipeline
from app.seed.corpus import seed_corpus_if_empty

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configure X-Ray
xray_recorder.configure(
    service="rag-backend",
    daemon_address=os.environ.get("AWS_XRAY_DAEMON_ADDRESS", "localhost:2000"),
    context_missing="LOG_ERROR"
)
patch_all()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting application")
    
    # Initialize database
    init_db()
    
    # Seed corpus if empty
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        seed_corpus_if_empty(db)
    finally:
        db.close()
    
    yield
    
    logger.info("Shutting down application")


app = FastAPI(
    title="RAG Backend API",
    description="Retrieval-Augmented Generation backend service",
    version="1.0.0",
    lifespan=lifespan
)

# Add X-Ray middleware
app.add_middleware(XRayMiddleware, recorder=xray_recorder)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, db: Session = Depends(get_db)):
    """Query RAG system."""
    logger.info("Received query", query=request.query[:50])
    
    try:
        pipeline = RAGPipeline(db)
        result = pipeline.query(request.query, top_k=request.top_k)
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            query=result["query"]
        )
    except Exception as e:
        logger.error("Query failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    try:
        vector_store = VectorStore(db)
        chunk_count = vector_store.get_chunk_count()
        
        return {
            "chunk_count": chunk_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Stats failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/docs")
async def get_api_docs():
    """Get API documentation link."""
    return {
        "openapi_url": "/openapi.json",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)