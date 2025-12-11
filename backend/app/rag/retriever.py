import structlog
from typing import List, Dict, Any

from app.db.vector_store import VectorStore
from app.rag.embeddings import BedrockEmbeddings

logger = structlog.get_logger()


class Retriever:
    """Retrieve relevant document chunks for a query."""
    
    def __init__(self, conn):
        self.vector_store = VectorStore(conn)
        self.embeddings = BedrockEmbeddings()
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve top-k relevant chunks for a query."""
        logger.info("Retrieving documents", query=query[:50], top_k=top_k)
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_text(query)
            
            # Search vector store
            results = self.vector_store.similarity_search(query_embedding, top_k=top_k)
            
            # Filter out results with very low similarity scores
            filtered_results = [
                result for result in results 
                if result.get('similarity', 0) > 0.1  # Minimum similarity threshold
            ]
            
            logger.info("Retrieved documents", 
                       total_results=len(results), 
                       filtered_results=len(filtered_results),
                       min_similarity=min([r.get('similarity', 0) for r in filtered_results]) if filtered_results else 0)
            
            return filtered_results
            
        except Exception as e:
            logger.error("Failed to retrieve documents", error=str(e), query=query[:50])
            raise
    
    def retrieve_with_metadata_filter(self, query: str, top_k: int = 5, 
                                  metadata_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve chunks with optional metadata filtering."""
        logger.info("Retrieving with filter", query=query[:50], top_k=top_k, filter=metadata_filter)
        
        # First get basic retrieval results
        results = self.retrieve(query, top_k * 2)  # Get more to account for filtering
        
        if not metadata_filter:
            return results[:top_k]
        
        # Apply metadata filtering
        filtered_results = []
        for result in results:
            result_metadata = result.get('metadata', {})
            
            # Simple metadata matching - all filter keys must match
            matches = True
            for key, value in metadata_filter.items():
                if result_metadata.get(key) != value:
                    matches = False
                    break
            
            if matches:
                filtered_results.append(result)
        
        logger.info("Applied metadata filter", 
                   before_count=len(results), 
                   after_count=len(filtered_results))
        
        return filtered_results[:top_k]
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        return self.vector_store.get_document_chunks(document_id)