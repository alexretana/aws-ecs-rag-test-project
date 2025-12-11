import uuid
from typing import List, Dict, Any
import structlog

from app.rag.embeddings import BedrockEmbeddings
from app.rag.retriever import Retriever
from app.rag.generator import BedrockGenerator
from app.db.vector_store import VectorStore
from app.config import get_settings

logger = structlog.get_logger()


class RAGPipeline:
    """Full RAG pipeline: retrieve and generate."""
    
    def __init__(self, conn):
        self.retriever = Retriever(conn)
        self.generator = BedrockGenerator()
        self.embeddings = BedrockEmbeddings()
        self.vector_store = VectorStore(conn)
        self.settings = get_settings()
    
    def query(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """Execute RAG query: retrieve relevant docs and generate response."""
        if top_k is None:
            top_k = self.settings.top_k_results
        
        logger.info("Executing RAG query", query=query[:50], top_k=top_k)
        
        try:
            # Retrieve relevant chunks
            chunks = self.retriever.retrieve(query, top_k=top_k)
            
            if not chunks:
                return {
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": [],
                    "query": query
                }
            
            # Generate response
            answer = self.generator.generate(query, chunks)
            
            # Format sources
            sources = [
                {
                    "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                    "metadata": chunk["metadata"],
                    "similarity": round(chunk["similarity"], 3)
                }
                for chunk in chunks
            ]
            
            result = {
                "answer": answer,
                "sources": sources,
                "query": query
            }
            
            logger.info("RAG query completed", 
                       sources_count=len(sources),
                       answer_length=len(answer))
            
            return result
            
        except Exception as e:
            logger.error("RAG query failed", error=str(e), query=query[:50])
            raise
    
    def ingest_document(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Ingest a document: chunk, embed, and store."""
        document_id = str(uuid.uuid4())
        metadata = metadata or {}
        
        # Simple chunking by paragraphs/sentences
        chunks = self._chunk_text(content)
        
        logger.info("Ingesting document", document_id=document_id, chunk_count=len(chunks))
        
        try:
            # Prepare chunks for batch insertion
            chunks_data = []
            for chunk in chunks:
                embedding = self.embeddings.embed_text(chunk)
                chunks_data.append({
                    'content': chunk,
                    'embedding': embedding,
                    'metadata': {
                        **metadata,
                        'document_id': document_id,
                        'chunk_index': len(chunks_data)
                    }
                })
            
            # Batch insert for better performance
            chunk_ids = self.vector_store.batch_add_chunks(document_id, chunks_data)
            
            # Create vector index if we have enough data
            if self.vector_store.get_chunk_count() >= 1000:
                self.vector_store.create_vector_index()
            
            logger.info("Document ingested successfully", 
                       document_id=document_id, 
                       chunk_count=len(chunk_ids))
            
            return document_id
            
        except Exception as e:
            logger.error("Failed to ingest document", error=str(e), document_id=document_id)
            raise
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        chunk_size = self.settings.chunk_size
        overlap = self.settings.chunk_overlap
        
        # Simple character-based chunking
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        # Remove empty chunks and very short chunks
        chunks = [c for c in chunks if c and len(c) > 50]
        
        logger.debug("Text chunked", original_length=len(text), chunk_count=len(chunks))
        return chunks
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks."""
        try:
            deleted_count = self.vector_store.delete_by_document_id(document_id)
            logger.info("Document deleted", document_id=document_id, chunks_deleted=deleted_count)
            return True
        except Exception as e:
            logger.error("Failed to delete document", error=str(e), document_id=document_id)
            return False
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document chunks by document ID."""
        try:
            chunks = self.vector_store.get_document_chunks(document_id)
            return {
                "document_id": document_id,
                "chunks": chunks,
                "chunk_count": len(chunks)
            }
        except Exception as e:
            logger.error("Failed to get document", error=str(e), document_id=document_id)
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        try:
            total_chunks = self.vector_store.get_chunk_count()
            return {
                "total_chunks": total_chunks,
                "embedding_model": self.settings.embedding_model_id,
                "llm_model": self.settings.llm_model_id,
                "chunk_size": self.settings.chunk_size,
                "chunk_overlap": self.settings.chunk_overlap
            }
        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return {}