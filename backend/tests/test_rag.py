import pytest
import asyncio
from unittest.mock import Mock, patch

from app.rag.pipeline import RAGPipeline
from app.rag.embeddings import BedrockEmbeddings
from app.rag.generator import BedrockGenerator
from app.rag.retriever import Retriever
from app.db.vector_store import VectorStore


class MockConnection:
    """Mock database connection for testing."""
    def __init__(self):
        self.data = {}
        self.closed = False
    
    def cursor(self):
        return MockCursor(self)
    
    def commit(self):
        pass
    
    def close(self):
        self.closed = True


class MockCursor:
    """Mock database cursor for testing."""
    def __init__(self, conn):
        self.conn = conn
    
    def execute(self, query, params=None):
        # Mock different query responses based on query content
        if "CREATE EXTENSION" in query:
            return None
        elif "CREATE TABLE" in query:
            return None
        elif "INSERT" in query:
            return None
        elif "SELECT COUNT" in query:
            return {"count": 0}
        elif "DELETE" in query:
            return {"rowcount": 1}
        elif "SELECT" in query and "document_chunks" in query:
            return []
        elif "SELECT" in query and "embedding" in query:
            # Mock similarity search results
            return [
                {
                    "id": "test-chunk-1",
                    "document_id": "test-doc-1",
                    "content": "Test content about machine learning",
                    "metadata": {"category": "AI/ML"},
                    "similarity": 0.85
                },
                {
                    "id": "test-chunk-2",
                    "document_id": "test-doc-2",
                    "content": "Test content about cloud computing",
                    "metadata": {"category": "Cloud"},
                    "similarity": 0.75
                }
            ]
        return None
    
    def fetchone(self):
        return None
    
    def fetchall(self):
        return []


@pytest.fixture
async def mock_db():
    """Create a mock database connection."""
    return MockConnection()


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    class MockSettings:
        aws_region = "us-east-1"
        embedding_model_id = "amazon.titan-embed-text-v1"
        llm_model_id = "meta.llama3-8b-instruct-v1:0"
        chunk_size = 500
        chunk_overlap = 50
        top_k_results = 5
    return MockSettings()


class TestBedrockEmbeddings:
    """Test Bedrock embeddings functionality."""
    
    @pytest.mark.asyncio
    async def test_embed_text_success(self, mock_settings):
        """Test successful text embedding."""
        with patch('app.rag.embeddings.boto3.client') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            
            # Mock successful response
            mock_response = Mock()
            mock_response["body"].read.return_value = json.dumps({
                "embedding": [0.1] * 1536  # Mock 1536-dimensional vector
            })
            mock_instance.invoke_model.return_value = mock_response
            
            embeddings = BedrockEmbeddings()
            result = await embeddings.embed_text("test text")
            
            assert len(result) == 1536
            assert all(isinstance(x, float) for x in result)
    
    @pytest.mark.asyncio
    async def test_embed_text_failure(self, mock_settings):
        """Test embedding generation failure."""
        with patch('app.rag.embeddings.boto3.client') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            
            # Mock failed response
            mock_instance.invoke_model.side_effect = Exception("Bedrock error")
            
            embeddings = BedrockEmbeddings()
            
            with pytest.raises(Exception):
                await embeddings.embed_text("test text")


class TestRetriever:
    """Test document retrieval functionality."""
    
    @pytest.mark.asyncio
    async def test_retrieve_success(self, mock_db, mock_settings):
        """Test successful document retrieval."""
        with patch('app.rag.retriever.BedrockEmbeddings') as mock_embeddings:
            mock_embeddings_instance = Mock()
            mock_embeddings.return_value = mock_embeddings_instance
            
            retriever = Retriever(mock_db)
            result = await retriever.retrieve("test query", top_k=3)
            
            assert len(result) == 2
            assert all("similarity" in chunk for chunk in result)
            assert result[0]["similarity"] > result[1]["similarity"]
    
    @pytest.mark.asyncio
    async def test_retrieve_empty_result(self, mock_db, mock_settings):
        """Test retrieval with no results."""
        with patch('app.rag.retriever.BedrockEmbeddings') as mock_embeddings:
            mock_embeddings_instance = Mock()
            mock_embeddings.return_value = mock_embeddings_instance
            
            # Mock empty similarity search
            mock_db.cursor.return_value.fetchall.return_value = []
            
            retriever = Retriever(mock_db)
            result = await retriever.retrieve("test query")
            
            assert len(result) == 0


class TestBedrockGenerator:
    """Test LLM generation functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_success(self, mock_settings):
        """Test successful response generation."""
        with patch('app.rag.generator.boto3.client') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            
            # Mock successful response
            mock_response = Mock()
            mock_response["body"].read.return_value = json.dumps({
                "generation": "This is a test response about machine learning."
            })
            mock_instance.invoke_model.return_value = mock_response
            
            generator = BedrockGenerator()
            result = await generator.generate("test query", [
                {"content": "Machine learning is a subset of AI."}
            ])
            
            assert "machine learning" in result
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_generate_no_context(self, mock_settings):
        """Test generation with no context."""
        with patch('app.rag.generator.boto3.client') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            
            generator = BedrockGenerator()
            result = await generator.generate("test query", [])
            
            assert "couldn't find any relevant information" in result


class TestRAGPipeline:
    """Test complete RAG pipeline functionality."""
    
    @pytest.mark.asyncio
    async def test_query_success(self, mock_db, mock_settings):
        """Test successful RAG query."""
        with patch('app.rag.pipeline.Retriever') as mock_retriever_class, \
             patch('app.rag.pipeline.BedrockGenerator') as mock_generator_class:
            
            # Mock retriever
            mock_retriever = Mock()
            mock_retriever_instance = Mock()
            mock_retriever.return_value = mock_retriever_instance
            mock_retriever_instance.retrieve.return_value = [
                {
                    "content": "Machine learning enables systems to learn.",
                    "metadata": {"category": "AI/ML"},
                    "similarity": 0.9
                }
            ]
            
            # Mock generator
            mock_generator = Mock()
            mock_generator_instance = Mock()
            mock_generator.return_value = mock_generator_instance
            mock_generator_instance.generate.return_value = "Based on the context, machine learning is a subset of AI."
            
            mock_retriever_class.return_value = mock_retriever
            mock_generator_class.return_value = mock_generator
            
            pipeline = RAGPipeline(mock_db)
            result = await pipeline.query("What is machine learning?")
            
            assert "answer" in result
            assert "sources" in result
            assert len(result["sources"]) == 1
            assert "machine learning" in result["answer"]
    
    @pytest.mark.asyncio
    async def test_ingest_document(self, mock_db, mock_settings):
        """Test document ingestion."""
        with patch('app.rag.pipeline.BedrockEmbeddings') as mock_embeddings:
            mock_embeddings_instance = Mock()
            mock_embeddings.return_value = mock_embeddings_instance
            mock_embeddings_instance.embed_text.return_value = [0.1] * 1536
            
            pipeline = RAGPipeline(mock_db)
            document_id = await pipeline.ingest_document(
                "Test document content",
                {"title": "Test Document", "category": "Test"}
            )
            
            assert document_id is not None
            assert len(document_id) > 0
    
    @pytest.mark.asyncio
    async def test_get_stats(self, mock_db, mock_settings):
        """Test statistics retrieval."""
        pipeline = RAGPipeline(mock_db)
        stats = await pipeline.get_stats()
        
            assert "total_chunks" in stats
            assert "embedding_model" in stats
            assert "llm_model" in stats


if __name__ == "__main__":
    pytest.main([__file__])