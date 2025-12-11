import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import QueryRequest, QueryResponse, HealthResponse


class TestAPI:
    """Test API endpoints."""
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        with TestClient(app) as client:
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert data["version"] == "1.0.0"
    
    def test_query_endpoint_success(self):
        """Test successful query endpoint."""
        mock_query_response = {
            "answer": "This is a test answer about machine learning.",
            "sources": [
                {
                    "content": "Machine learning is a subset of AI...",
                    "metadata": {"category": "AI/ML"},
                    "similarity": 0.9
                }
            ],
            "query": "What is machine learning?"
        }
        
        with patch('app.rag.pipeline.RAGPipeline.query') as mock_query:
            mock_query.return_value = mock_query_response
            
            with TestClient(app) as client:
                response = client.post(
                    "/api/query",
                    json={"query": "What is machine learning?", "top_k": 3}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["answer"] == "This is a test answer about machine learning."
                assert len(data["sources"]) == 1
                assert data["query"] == "What is machine learning?"
    
    def test_query_endpoint_invalid_request(self):
        """Test query endpoint with invalid request."""
        with TestClient(app) as client:
            # Missing query field
            response = client.post("/api/query", json={"top_k": 3})
            
            assert response.status_code == 422  # Validation error
    
    def test_stats_endpoint(self):
        """Test statistics endpoint."""
        mock_stats_response = {
            "chunk_count": 150,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        with patch('app.db.vector_store.VectorStore.get_chunk_count') as mock_count:
            mock_count.return_value = 150
            
            with TestClient(app) as client:
                response = client.get("/api/stats")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["chunk_count"] == 150
                assert "timestamp" in data
    
    def test_api_docs_endpoint(self):
        """Test API documentation endpoint."""
        with TestClient(app) as client:
            response = client.get("/api/docs")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "openapi_url" in data
            assert "docs_url" in data
            assert "redoc_url" in data
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        with TestClient(app) as client:
            response = client.options("/api/query")
            
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-methods" in response.headers
            assert "access-control-allow-headers" in response.headers


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.mark.asyncio
    async def test_full_query_flow(self):
        """Test complete query flow with mocked dependencies."""
        # Mock all the dependencies
        with patch('app.get_db') as mock_get_db, \
             patch('app.rag.pipeline.RAGPipeline') as mock_pipeline_class:
            
            # Mock database connection
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn
            
            # Mock pipeline instance
            mock_pipeline_instance = Mock()
            mock_pipeline_class.return_value = mock_pipeline_instance
            
            # Mock query method
            mock_pipeline_instance.query.return_value = {
                "answer": "Machine learning enables systems to learn.",
                "sources": [
                    {
                        "content": "ML is a subset of AI...",
                        "similarity": 0.85
                    }
                ],
                "query": "What is ML?"
            }
            
            # Import here to avoid circular imports in test
            from app.main import query
            
            # Call the actual endpoint
            result = await query(
                QueryRequest(query="What is ML?", top_k=3),
                db=mock_conn
            )
            
            assert result.answer == "Machine learning enables systems to learn."
            assert len(result.sources) == 1
            assert result.query == "What is ML?"


if __name__ == "__main__":
    pytest.main([__file__])