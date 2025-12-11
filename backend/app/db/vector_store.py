import uuid
from typing import List, Optional, Dict, Any
import structlog

from app.db.database import get_db, acquire_advisory_lock, release_advisory_lock

logger = structlog.get_logger()


class VectorStore:
    """Vector store for document embeddings using pgvector."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def add_chunk(self, document_id: str, content: str, embedding: List[float], metadata: Dict[str, Any] = None) -> str:
        """Add a document chunk with its embedding."""
        chunk_id = str(uuid.uuid4())
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO document_chunks (id, document_id, content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (chunk_id, document_id, content, embedding, metadata or {}))
            self.conn.commit()
            
        logger.debug("Added chunk", chunk_id=chunk_id, document_id=document_id)
        return chunk_id
    
    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar document chunks using cosine similarity."""
        with self.conn.cursor() as cur:
            # Use <=> operator for cosine similarity
            # 1 - (embedding <=> query_embedding) gives cosine similarity
            cur.execute("""
                SELECT 
                    id,
                    document_id,
                    content,
                    metadata,
                    created_at,
                    1 - (embedding <=> %s) as similarity
                FROM document_chunks
                ORDER BY embedding <=> %s
                LIMIT %s
            """, (query_embedding, query_embedding, top_k))
            
            results = cur.fetchall()
            
        logger.debug("Similarity search completed", results_count=len(results), top_k=top_k)
            return results
    
    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all chunks for a document."""
        with self.conn.cursor() as cur:
            cur.execute("""
                DELETE FROM document_chunks
                WHERE document_id = %s
            """, (document_id,))
            deleted_count = cur.rowcount
            self.conn.commit()
            
        logger.info("Deleted chunks", document_id=document_id, count=deleted_count)
        return deleted_count
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks in the database."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM document_chunks")
            result = cur.fetchone()
            return result['count'] if result else 0
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, content, metadata, created_at
                FROM document_chunks
                WHERE document_id = %s
                ORDER BY created_at
            """, (document_id,))
            return cur.fetchall()
    
    def batch_add_chunks(self, document_id: str, chunks_data: List[Dict[str, Any]]) -> List[str]:
        """Add multiple chunks in a single transaction for better performance."""
        chunk_ids = []
        
        with self.conn.cursor() as cur:
            for chunk_data in chunks_data:
                chunk_id = str(uuid.uuid4())
                chunk_ids.append(chunk_id)
                
                cur.execute("""
                    INSERT INTO document_chunks (id, document_id, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    chunk_id,
                    document_id,
                    chunk_data['content'],
                    chunk_data['embedding'],
                    chunk_data.get('metadata', {})
                ))
            
            self.conn.commit()
            
        logger.info("Batch added chunks", document_id=document_id, count=len(chunk_ids))
        return chunk_ids
    
    def create_vector_index(self):
        """Create or recreate vector index for better search performance."""
        with self.conn.cursor() as cur:
            # Drop existing index if it exists
            cur.execute("DROP INDEX IF EXISTS idx_document_chunks_embedding")
            
            # Create new index with ivfflat for better performance
            # Only create if we have enough data (at least 1000 rows)
            cur.execute("SELECT COUNT(*) FROM document_chunks")
            count = cur.fetchone()['count']
            
            if count >= 1000:
                cur.execute("""
                    CREATE INDEX idx_document_chunks_embedding 
                    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = %s)
                """, (min(count // 1000, 100)))
                logger.info("Created ivfflat index", lists=min(count // 1000, 100))
            else:
                logger.info("Skipping vector index creation (insufficient data)", count=count)
            
            self.conn.commit()