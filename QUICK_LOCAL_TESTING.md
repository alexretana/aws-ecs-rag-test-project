# Quick Local Testing Guide

This is a simplified guide to get your RAG application running locally for testing before AWS deployment.

## Prerequisites

1. Docker and Docker Compose installed
2. Git repository cloned locally

## Option 1: Simple Local Testing (Recommended for Quick Testing)

### Step 1: Create docker-compose.yml

Create this file in your project root:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: rag_db
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: rag_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rag_user -d rag_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=rag_db
      - DB_USERNAME=rag_user
      - DB_PASSWORD=rag_password
      - AWS_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - EMBEDDING_MODEL_ID=amazon.titan-embed-text-v1
      - LLM_MODEL_ID=meta.llama3-8b-instruct-v1:0
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    environment:
      - BACKEND_URL=http://backend:8000
    ports:
      - "8501:8501"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
    command: streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true

volumes:
  postgres_data:
```

### Step 2: Update Backend Configuration

Update `backend/app/config.py` to use environment variables:

```python
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "local"
    aws_region: str = "us-east-1"
    
    # Database settings from environment
    db_host: str = os.environ.get("DB_HOST", "localhost")
    db_port: int = int(os.environ.get("DB_PORT", 5432))
    db_name: str = os.environ.get("DB_NAME", "rag_db")
    db_username: str = os.environ.get("DB_USERNAME", "rag_user")
    db_password: str = os.environ.get("DB_PASSWORD", "rag_password")
    
    # AWS settings from environment
    aws_access_key_id: str = os.environ.get("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    
    # Bedrock settings
    embedding_model_id: str = "amazon.titan-embed-text-v1"
    llm_model_id: str = "meta.llama3-8b-instruct-v1:0"
    
    # RAG settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### Step 3: Create Mock AWS Services

Create `backend/app/mocks/__init__.py`:

```python
# Empty file to make it a Python package
```

Create `backend/app/mocks/aws_services.py`:

```python
import json
import numpy as np
import boto3
from botocore.client import BaseClient

class MockBedrockRuntime(BaseClient):
    """Mock Bedrock Runtime for local testing."""
    
    def invoke_model(self, modelId, body, **kwargs):
        request_body = json.loads(body)
        
        if "titan-embed" in modelId.lower():
            # Generate consistent mock embeddings based on text hash
            text = request_body.get("inputText", "")
            # Create deterministic embeddings based on text
            seed = hash(text) % (2**32)
            np.random.seed(seed)
            embedding = np.random.rand(1536).tolist()
            
            return {
                "body": type('MockBody', (), {
                    "read": lambda: json.dumps({"embedding": embedding})
                })()
            }
        elif "llama" in modelId.lower():
            # Generate contextual responses
            prompt = request_body.get("prompt", "")
            
            # Extract context from prompt for better responses
            if "machine learning" in prompt.lower():
                response = "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed."
            elif "cloud computing" in prompt.lower():
                response = "Cloud computing is the delivery of computing services over the Internet to offer faster innovation, flexible resources, and economies of scale."
            elif "kubernetes" in prompt.lower():
                response = "Kubernetes is an open-source container orchestration platform that automates deployment, scaling, and management of containerized applications."
            elif "rag" in prompt.lower() or "retrieval" in prompt.lower():
                response = "Retrieval-Augmented Generation (RAG) is an AI framework that enhances large language models by retrieving relevant information from external knowledge sources before generating responses."
            else:
                response = "Based on the provided context, this appears to be related to modern technology concepts. The specific answer would depend on the detailed context provided in the documents."
            
            return {
                "body": type('MockBody', (), {
                    "read": lambda: json.dumps({"generation": response})
                })()
            }
        
        return {
            "body": type('MockBody', (), {
                "read": lambda: json.dumps({})
            })()
        }

# Mock boto3 client function
def mock_boto3_client(service_name, **kwargs):
    if service_name == "bedrock-runtime":
        return MockBedrockRuntime(
            service_name=service_name,
            region_name=kwargs.get('region_name', 'us-east-1')
        )
    return boto3.client(service_name, **kwargs)
```

### Step 4: Update Embeddings and Generator Classes

Update `backend/app/rag/embeddings.py`:

```python
import json
import os
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()

class BedrockEmbeddings:
    """Generate embeddings using AWS Bedrock or mock for local testing."""
    
    def __init__(self):
        settings = get_settings()
        
        # Use mock for local testing
        if os.environ.get("ENVIRONMENT", "local") == "local":
            from app.mocks.aws_services import mock_boto3_client
            self.client = mock_boto3_client(
                "bedrock-runtime",
                region_name=settings.aws_region
            )
        else:
            import boto3
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region
            )
        
        self.model_id = settings.embedding_model_id
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_text(self, text: str) -> list:
        """Generate embedding for a single text."""
        body = json.dumps({
            "inputText": text
        })
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])
            
            logger.debug("Generated embedding", text_length=len(text), embedding_dim=len(embedding))
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e), text_length=len(text))
            raise
    
    def embed_texts(self, texts: list) -> list:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
                logger.debug("Processed text", index=i, total=len(texts))
            except Exception as e:
                logger.error("Failed to embed text", index=i, error=str(e))
                raise
        
        logger.info("Generated embeddings", count=len(embeddings))
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model."""
        return 1536
```

Update `backend/app/rag/generator.py` similarly:

```python
import json
import os
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()

class BedrockGenerator:
    """Generate responses using AWS Bedrock or mock for local testing."""
    
    def __init__(self):
        settings = get_settings()
        
        # Use mock for local testing
        if os.environ.get("ENVIRONMENT", "local") == "local":
            from app.mocks.aws_services import mock_boto3_client
            self.client = mock_boto3_client(
                "bedrock-runtime",
                region_name=settings.aws_region
            )
        else:
            import boto3
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region
            )
        
        self.model_id = settings.llm_model_id
    
    def _build_prompt(self, query: str, context_chunks: list) -> str:
        """Build prompt with retrieved context."""
        context = "\n\n".join([
            f"Document {i+1}:\n{chunk['content']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant. Answer the user's question based on the provided context. 
If the context doesn't contain enough information to answer the question, say so.
Be concise and accurate in your responses.
Only use information from the provided context.

Context:
{context}
<|eot_id|><|start_header_id|>user<|end_header_id|>

{query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        return prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, query: str, context_chunks: list) -> str:
        """Generate response using retrieved context."""
        if not context_chunks:
            return "I couldn't find any relevant information to answer your question."
        
        prompt = self._build_prompt(query, context_chunks)
        
        try:
            logger.info("Generating response", query=query[:50], context_chunks=len(context_chunks))
            
            body = json.dumps({
                "prompt": prompt,
                "max_gen_len": 512,
                "temperature": 0.7,
                "top_p": 0.9,
            })
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            generated_text = response_body.get("generation", "")
            
            logger.info("Generated response", response_length=len(generated_text))
            return generated_text.strip()
            
        except Exception as e:
            logger.error("Failed to generate response", error=str(e), query=query[:50])
            raise
    
    def generate_with_streaming(self, query: str, context_chunks: list):
        """Generate response with streaming (for future implementation)."""
        return self.generate(query, context_chunks)
    
    def _extract_citations(self, response: str, context_chunks: list) -> list:
        """Extract citations from generated response (placeholder for future enhancement)."""
        return []
```

### Step 5: Start the Environment

1. Start the services:
```bash
docker-compose up -d
```

2. Wait for services to be ready (about 30 seconds):
```bash
docker-compose ps
```

3. Check if backend is healthy:
```bash
curl http://localhost:8000/health
```

### Step 6: Test the Application

1. **Access the Frontend**: Open http://localhost:8501 in your browser

2. **Test the API directly**:
```bash
# Check health
curl http://localhost:8000/health

# Test a query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 3}'

# Check stats
curl http://localhost:8000/api/stats
```

3. **Test with the Frontend**:
   - Open http://localhost:8501
   - Ask questions like:
     - "What is machine learning?"
     - "Explain cloud computing"
     - "What is Kubernetes?"
     - "How does RAG work?"

### Step 7: Stop the Environment

```bash
docker-compose down
```

## Option 2: Local Testing with Real AWS Services

If you want to use real AWS Bedrock services but with a local database:

### Step 1: Configure AWS Credentials

Set up your AWS credentials:
```bash
aws configure
```

### Step 2: Update docker-compose.yml

Remove the LocalStack service and update the backend environment:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: rag_db
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: rag_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rag_user -d rag_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=rag_db
      - DB_USERNAME=rag_user
      - DB_PASSWORD=rag_password
      - AWS_REGION=us-east-1
      - ENVIRONMENT=dev
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ~/.aws:/root/.aws:ro  # Mount AWS credentials
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    environment:
      - BACKEND_URL=http://backend:8000
    ports:
      - "8501:8501"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
    command: streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true

volumes:
  postgres_data:
```

### Step 3: Update Backend Configuration

Ensure your `backend/app/config.py` properly loads AWS credentials from the default credential chain.

## Testing Checklist

Before pushing to production, verify:

- [ ] Backend health endpoint returns 200
- [ ] Frontend loads without errors
- [ ] Query endpoint returns relevant responses
- [ ] Sources are displayed with similarity scores
- [ ] Database is properly seeded with sample documents
- [ ] Vector similarity search works correctly
- [ ] Error handling works for invalid queries
- [ ] CORS headers are properly set

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Check database connection
docker-compose exec postgres psql -U rag_user -d rag_db
```

### Frontend can't connect to backend
- Verify backend is running: `curl http://localhost:8000/health`
- Check if ports are exposed correctly in docker-compose.yml
- Verify BACKEND_URL environment variable in frontend

### No search results
- Check if database is seeded: `curl http://localhost:8000/api/stats`
- Verify embeddings are being generated
- Check vector similarity search in logs

### AWS Service Issues
- Verify AWS credentials are configured
- Check if Bedrock models are available in your region
- Review IAM permissions

## Next Steps

Once local testing is complete:

1. Run the full test suite
2. Test with larger datasets
3. Verify all API endpoints
4. Check error handling
5. Deploy to AWS ECS

This local testing setup should give you confidence that your application works correctly before deploying to AWS.