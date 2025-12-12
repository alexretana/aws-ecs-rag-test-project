# Local Development and Testing Guide

This guide provides a comprehensive approach to testing your AWS ECS RAG application locally before deploying to AWS.

## Overview

The local testing environment includes:
- PostgreSQL with pgvector extension for vector storage
- LocalStack for mocking AWS services (Bedrock, Secrets Manager)
- Backend FastAPI application
- Frontend Streamlit application
- Mock implementations for AWS services

## Prerequisites

1. Docker and Docker Compose installed
2. Git for cloning the repository
3. Python 3.11+ (for running tests locally)
4. AWS CLI (configured with dummy credentials for LocalStack)

## Step 1: Create Docker Compose Configuration

Create a `docker-compose.yml` file in your project root:

```yaml
version: '3.8'

services:
  # PostgreSQL with pgvector extension for vector storage
  postgres:
    image: pgvector/pgvector:pg15
    container_name: rag-postgres
    environment:
      POSTGRES_DB: rag_db
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: rag_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./local-dev/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rag_user -d rag_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - rag-network

  # LocalStack for mocking AWS services
  localstack:
    image: localstack/localstack:latest
    container_name: rag-localstack
    ports:
      - "4566:4566"  # LocalStack edge port
      - "4510-4559:4510-4559"  # Service-specific ports
    environment:
      - DEBUG=1
      - SERVICES=bedrock,secretsmanager
      - DATA_DIR=/tmp/localstack/data
      - DOCKER_HOST=unix:///var/run/docker.sock
      - AWS_DEFAULT_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
    volumes:
      - localstack_data:/tmp/localstack
      - ./local-dev/localstack-setup:/docker-entrypoint-initaws.d
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - rag-network

  # Backend FastAPI application
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: rag-backend
    environment:
      - ENVIRONMENT=local
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=rag_db
      - DB_USERNAME=rag_user
      - DB_PASSWORD=rag_password
      - AWS_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - AWS_ENDPOINT_URL=http://localstack:4566
      - EMBEDDING_MODEL_ID=amazon.titan-embed-text-v1
      - LLM_MODEL_ID=meta.llama3-8b-instruct-v1:0
      - CHUNK_SIZE=500
      - CHUNK_OVERLAP=50
      - TOP_K_RESULTS=5
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      localstack:
        condition: service_started
    volumes:
      - ./backend:/app
    networks:
      - rag-network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend Streamlit application
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: rag-frontend
    environment:
      - BACKEND_URL=http://backend:8000
    ports:
      - "8501:8501"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
    networks:
      - rag-network
    command: streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true

volumes:
  postgres_data:
  localstack_data:

networks:
  rag-network:
    driver: bridge
```

## Step 2: Create Local Development Directory Structure

Create the following directory structure:

```
local-dev/
├── init-db.sql
├── localstack-setup/
│   ├── setup-bedrock.sh
│   └── setup-secrets.sh
├── mock-services/
│   ├── __init__.py
│   ├── mock_bedrock.py
│   └── mock_secrets.py
└── scripts/
    ├── start-dev.sh
    ├── stop-dev.sh
    ├── test-backend.sh
    └── seed-data.sh
```

## Step 3: Database Initialization Script

Create `local-dev/init-db.sql`:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create document_chunks table with vector support
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on document_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id 
ON document_chunks(document_id);

-- Create vector index for similarity search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Step 4: LocalStack Setup Scripts

Create `local-dev/localstack-setup/setup-bedrock.sh`:

```bash
#!/bin/bash
# Setup mock Bedrock models in LocalStack

aws --endpoint-url=http://localhost:4566 bedrock create-custom-model \
    --model-name amazon.titan-embed-text-v1 \
    --base-model-identifier amazon.titan-embed-text-v1 \
    --model-kvp-key ModelType=embedding \
    --model-kvp-value EmbeddingModel || true

aws --endpoint-url=http://localhost:4566 bedrock create-custom-model \
    --model-name meta.llama3-8b-instruct-v1:0 \
    --base-model-identifier meta.llama3-8b-instruct-v1:0 \
    --model-kvp-key ModelType=generation \
    --model-kvp-value GenerationModel || true
```

Create `local-dev/localstack-setup/setup-secrets.sh`:

```bash
#!/bin/bash
# Setup database credentials in Secrets Manager

aws --endpoint-url=http://localhost:4566 secretsmanager create-secret \
    --name rag-db-credentials \
    --secret-string '{
        "host": "postgres",
        "port": 5432,
        "dbname": "rag_db",
        "username": "rag_user",
        "password": "rag_password"
    }' || true
```

## Step 5: Mock AWS Services

Create `local-dev/mock-services/mock_bedrock.py`:

```python
import json
import numpy as np
from typing import Dict, Any

class MockBedrockRuntime:
    """Mock Bedrock Runtime for local development."""
    
    def invoke_model(self, modelId: str, body: str, contentType: str = "application/json", accept: str = "application/json") -> Dict[str, Any]:
        """Mock model invocation."""
        request_body = json.loads(body)
        
        if "titan-embed" in modelId.lower():
            # Mock embedding generation
            embedding = np.random.rand(1536).tolist()
            return {
                "body": {
                    "read": lambda: json.dumps({"embedding": embedding})
                }
            }
        elif "llama" in modelId.lower():
            # Mock text generation
            prompt = request_body.get("prompt", "")
            # Simple mock response based on prompt
            if "machine learning" in prompt.lower():
                response = "Machine learning is a subset of artificial intelligence that enables systems to learn from data."
            elif "cloud computing" in prompt.lower():
                response = "Cloud computing delivers computing services over the internet for better innovation and scalability."
            else:
                response = "This is a mock response generated locally for testing purposes."
            
            return {
                "body": {
                    "read": lambda: json.dumps({"generation": response})
                }
            }
        
        return {
            "body": {
                "read": lambda: json.dumps({})
            }
        }
```

Create `local-dev/mock-services/mock_secrets.py`:

```python
import json

class MockSecretsManager:
    """Mock Secrets Manager for local development."""
    
    def get_secret_value(self, SecretId: str) -> Dict[str, Any]:
        """Mock secret retrieval."""
        if SecretId == "rag-db-credentials":
            return {
                "SecretString": json.dumps({
                    "host": "localhost",
                    "port": 5432,
                    "dbname": "rag_db",
                    "username": "rag_user",
                    "password": "rag_password"
                })
            }
        return {"SecretString": "{}"}
```

## Step 6: Development Scripts

Create `local-dev/scripts/start-dev.sh`:

```bash
#!/bin/bash
# Start the local development environment

echo "Starting local development environment..."

# Create local-dev directory if it doesn't exist
mkdir -p local-dev

# Start Docker Compose
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check if services are running
docker-compose ps

echo "Local development environment started!"
echo "Frontend: http://localhost:8501"
echo "Backend API: http://localhost:8000"
echo "Backend Docs: http://localhost:8000/docs"
```

Create `local-dev/scripts/stop-dev.sh`:

```bash
#!/bin/bash
# Stop the local development environment

echo "Stopping local development environment..."

docker-compose down

echo "Local development environment stopped."
```

Create `local-dev/scripts/test-backend.sh`:

```bash
#!/bin/bash
# Test the backend API

echo "Testing backend API..."

# Health check
curl -f http://localhost:8000/health || echo "Health check failed"

# Test query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 3}' || echo "Query test failed"

# Test stats endpoint
curl -f http://localhost:8000/api/stats || echo "Stats test failed"

echo "Backend API tests completed."
```

Create `local-dev/scripts/seed-data.sh`:

```bash
#!/bin/bash
# Seed the database with sample data

echo "Seeding database with sample data..."

# Connect to backend container and seed data
docker-compose exec backend python -c "
from app.seed.corpus import seed_corpus_if_empty
from app.db.database import SessionLocal
db = SessionLocal()
try:
    seed_corpus_if_empty(db)
    print('Database seeded successfully')
finally:
    db.close()
"

echo "Database seeding completed."
```

## Step 7: Update Backend Configuration

Update `backend/app/config.py` to support local environment:

```python
import json
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment and AWS Secrets Manager."""
    
    # App settings
    environment: str = "dev"
    aws_region: str = "us-east-1"
    log_level: str = "INFO"
    
    # Database settings (loaded from secrets or environment)
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_username: str = ""
    db_password: str = ""
    
    # AWS settings
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_endpoint_url: str = ""
    
    # Bedrock settings
    embedding_model_id: str = "amazon.titan-embed-text-v1"
    llm_model_id: str = "meta.llama3-8b-instruct-v1:0"
    
    # RAG settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    
    class Config:
        env_prefix = ""


def load_db_credentials() -> dict:
    """Load database credentials from AWS Secrets Manager or environment."""
    # For local development, use environment variables
    if os.environ.get("ENVIRONMENT") == "local":
        return {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", 5432)),
            "dbname": os.environ.get("DB_NAME", "rag_db"),
            "username": os.environ.get("DB_USERNAME", "rag_user"),
            "password": os.environ.get("DB_PASSWORD", "rag_password")
        }
    
    # For production, load from Secrets Manager
    secret_json = os.environ.get("DB_SECRET")
    if secret_json:
        return json.loads(secret_json)
    return {}


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    settings = Settings()
    
    # Load DB credentials
    db_creds = load_db_credentials()
    if db_creds:
        settings.db_host = db_creds.get("host", "")
        settings.db_port = db_creds.get("port", 5432)
        settings.db_name = db_creds.get("dbname", "")
        settings.db_username = db_creds.get("username", "")
        settings.db_password = db_creds.get("password", "")
    
    # Load AWS credentials from environment
    settings.aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", "")
    settings.aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    settings.aws_endpoint_url = os.environ.get("AWS_ENDPOINT_URL", "")
    
    return settings
```

## Step 8: Update AWS Service Clients

Update `backend/app/rag/embeddings.py` to support local development:

```python
import json
import boto3
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
import os

from app.config import get_settings

logger = structlog.get_logger()


class BedrockEmbeddings:
    """Generate embeddings using AWS Bedrock Titan or mock for local development."""
    
    def __init__(self):
        settings = get_settings()
        
        # Use mock client for local development
        if os.environ.get("ENVIRONMENT") == "local":
            from local_dev.mock_services.mock_bedrock import MockBedrockRuntime
            self.client = MockBedrockRuntime()
        else:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                endpoint_url=settings.aws_endpoint_url
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

## Step 9: Running the Local Environment

### Starting the Environment

1. Make all scripts executable:
```bash
chmod +x local-dev/scripts/*.sh
chmod +x local-dev/localstack-setup/*.sh
```

2. Start the development environment:
```bash
./local-dev/scripts/start-dev.sh
```

3. Seed the database with sample data:
```bash
./local-dev/scripts/seed-data.sh
```

### Accessing the Applications

- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- Backend API Documentation: http://localhost:8000/docs
- LocalStack UI: http://localhost:4566

### Running Tests

1. Run backend tests:
```bash
docker-compose exec backend pytest
```

2. Run API tests manually:
```bash
./local-dev/scripts/test-backend.sh
```

3. Test the full RAG pipeline:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 3}'
```

### Stopping the Environment

```bash
./local-dev/scripts/stop-dev.sh
```

## Step 10: Testing Workflow

### 1. Unit Testing
Run unit tests for individual components:
```bash
docker-compose exec backend pytest backend/tests/test_rag.py -v
docker-compose exec backend pytest backend/tests/test_api.py -v
```

### 2. Integration Testing
Test the complete flow:
1. Access the frontend at http://localhost:8501
2. Ask questions about the sample documents
3. Verify responses include relevant sources

### 3. Performance Testing
Test with larger datasets:
```bash
# Add more documents via the API
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "Your document content here", "metadata": {"title": "Test Doc"}}'
```

### 4. Error Handling Testing
Test error scenarios:
- Invalid queries
- Empty database
- Network failures

## Troubleshooting

### Common Issues

1. **PostgreSQL Connection Issues**
   - Check if PostgreSQL container is running: `docker-compose ps postgres`
   - Verify connection settings in docker-compose.yml
   - Check logs: `docker-compose logs postgres`

2. **LocalStack Issues**
   - Verify LocalStack is running: `docker-compose ps localstack`
   - Check AWS service setup: `aws --endpoint-url=http://localhost:4566 ls`
   - Review LocalStack logs: `docker-compose logs localstack`

3. **Backend Issues**
   - Check backend logs: `docker-compose logs backend`
   - Verify environment variables
   - Test database connection manually

4. **Frontend Issues**
   - Check frontend logs: `docker-compose logs frontend`
   - Verify backend URL is accessible from frontend container
   - Check browser console for JavaScript errors

### Debugging Tips

1. **Check Container Logs**
```bash
docker-compose logs [service-name]
```

2. **Access Container Shell**
```bash
docker-compose exec [service-name] bash
```

3. **Test Database Connection**
```bash
docker-compose exec postgres psql -U rag_user -d rag_db
```

4. **Verify AWS Services in LocalStack**
```bash
aws --endpoint-url=http://localhost:4566 bedrock list-foundation-models
aws --endpoint-url=http://localhost:4566 secretsmanager list-secrets
```

## Next Steps

Once your local testing is complete:

1. Run the full test suite to ensure everything works
2. Test with production-like data volumes
3. Verify all API endpoints work correctly
4. Check error handling and edge cases
5. Document any issues found and fixes applied

After successful local testing, you'll be ready to deploy to AWS ECS with confidence that your application works as expected.