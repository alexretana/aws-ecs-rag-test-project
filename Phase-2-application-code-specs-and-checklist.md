# Phase 2: Application Code Specifications and Implementation Checklist

## Overview

This document outlines the specifications and implementation checklist for Phase 2 of the ECS RAG Test Project. It defines the exact technology stack, package requirements, and step-by-step implementation guide for the application code components.

## Technology Stack and Package Requirements

### Backend Dependencies

**IMPORTANT**: The following packages are the ONLY approved dependencies for Phase 2. No additional packages may be added or modified without explicit approval.

```txt
fastapi==0.109.2
uvicorn[standard]==0.27.1
pydantic==2.6.1
pydantic-settings==2.1.0
boto3==1.34.34
psycopg==3.3.2
httpx==0.26.0
structlog==24.1.0
python-multipart==0.0.9
tenacity==8.2.3
numpy==1.26.4
pytest==7.4.4
```

### Frontend Dependencies

```txt
streamlit==1.31.0
httpx==0.26.0
```

## Package Usage Guidelines

### Core Framework Decisions

1. **FastAPI**: Web framework for backend API
   - Use built-in dependency injection
   - Leverage automatic OpenAPI documentation
   - Implement async endpoints for better performance

2. **psycopg 3**: Direct PostgreSQL connection (NOT psycopg2)
   - Use connection pooling for efficiency
   - Implement proper connection management
   - Leverage async support where appropriate

3. **No ORM**: Explicitly forbidden
   - Direct SQL queries only
   - Use psycopg3's server-side cursor support
   - Implement custom data access layer

4. **pgvector**: Vector operations through psycopg3
   - Use native PostgreSQL vector extension
   - Implement similarity search with SQL
   - No external vector database services

5. **httpx**: HTTP client for external API calls
   - Use async client for non-blocking requests
   - Implement proper retry logic with tenacity
   - Use with boto3 for AWS authentication

6. **boto3**: AWS SDK for service integration
   - Bedrock API calls for embeddings and generation
   - Secrets Manager integration
   - X-Ray tracing integration

7. **pydantic**: Data validation and settings
   - Use pydantic-settings for configuration
   - Implement request/response models
   - Leverage type hints throughout

8. **structlog**: Structured logging
   - JSON-formatted logs for CloudWatch
   - Include correlation IDs
   - Integrate with X-Ray tracing

## Architecture Specifications

### Backend Application Structure

```
backend/
├── requirements.txt              # EXACT package versions as specified
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration with pydantic-settings
│   ├── models.py                # Pydantic models for API
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py          # psycopg3 connection management
│   │   └── vector_store.py     # pgvector operations
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py       # Bedrock Titan embeddings
│   │   ├── retriever.py        # Vector similarity search
│   │   ├── generator.py        # Bedrock Llama 3 generation
│   │   └── pipeline.py         # Complete RAG workflow
│   └── seed/
│       ├── __init__.py
│       ├── corpus.py           # Document seeding logic
│       └── data/
│           └── sample_documents.json
├── tests/
│   ├── __init__.py
│   ├── test_rag.py            # RAG pipeline tests
│   └── test_api.py            # API endpoint tests
├── Dockerfile
├── appspec.yml               # CodeDeploy specification
└── taskdef.json             # ECS task definition template
```

### Frontend Application Structure

```
frontend/
├── requirements.txt           # EXACT package versions as specified
├── app.py                  # Streamlit application
├── Dockerfile
├── appspec.yml             # CodeDeploy specification
└── taskdef.json           # ECS task definition template
```

## Implementation Checklist

### Phase 2.1: Backend Core Infrastructure

#### 2.1.1 Package Configuration
- [ ] Create `backend/requirements.txt` with EXACT package versions specified above
- [ ] Verify no additional packages are added during development
- [ ] Test package installation in clean environment

#### 2.1.2 Application Structure
- [ ] Create `backend/app/__init__.py`
- [ ] Create `backend/app/config.py` with:
  - Settings class using pydantic-settings
  - Database configuration from environment variables
  - AWS Bedrock configuration
  - RAG parameters (chunk size, top_k, etc.)
- [ ] Create `backend/app/models.py` with:
  - Document model for RAG corpus
  - QueryRequest and QueryResponse models
  - HealthResponse model
  - DocumentChunk model

### Phase 2.2: Database Layer

#### 2.2.1 Database Connection
- [ ] Create `backend/app/db/__init__.py`
- [ ] Create `backend/app/db/database.py` with:
  - psycopg3 connection pool configuration
  - Connection management functions
  - Advisory lock implementation for seeding
  - pgvector extension initialization
  - **IMPORTANT**: No SQLAlchemy or any ORM

#### 2.2.2 Vector Store Implementation
- [ ] Create `backend/app/db/vector_store.py` with:
  - DocumentChunkModel using direct SQL
  - VectorStore class with pgvector operations
  - Similarity search using vector operators
  - Chunk insertion and retrieval methods
  - Index creation for performance

### Phase 2.3: RAG Components

#### 2.3.1 Embeddings Service
- [ ] Create `backend/app/rag/__init__.py`
- [ ] Create `backend/app/rag/embeddings.py` with:
  - BedrockEmbeddings class using boto3
  - Titan text embedding integration
  - Batch embedding support
  - Retry logic with tenacity
  - Error handling and logging

#### 2.3.2 Retrieval Service
- [ ] Create `backend/app/rag/retriever.py` with:
  - Retriever class for document search
  - Integration with VectorStore
  - Query embedding generation
  - Top-k result selection
  - Similarity scoring

#### 2.3.3 Generation Service
- [ ] Create `backend/app/rag/generator.py` with:
  - BedrockGenerator class using boto3
  - Llama 3 8B Instruct integration
  - Prompt building with retrieved context
  - Response generation
  - Retry logic with tenacity

#### 2.3.4 RAG Pipeline
- [ ] Create `backend/app/rag/pipeline.py` with:
  - RAGPipeline class combining all components
  - Query method (retrieve + generate)
  - Document ingestion method (chunk + embed + store)
  - Text chunking implementation
  - End-to-end workflow orchestration

### Phase 2.4: Seed Data

#### 2.4.1 Sample Documents
- [ ] Create `backend/app/seed/__init__.py`
- [ ] Create `backend/app/seed/data/sample_documents.json` with:
  - 5-10 diverse documents
  - Topics: AI/ML, Cloud Computing, DevOps, Security
  - Metadata for categorization

#### 2.4.2 Corpus Seeding
- [ ] Create `backend/app/seed/corpus.py` with:
  - Document loading from JSON
  - RAGPipeline integration for ingestion
  - Advisory lock for race condition prevention
  - Error handling and progress logging

### Phase 2.5: API Implementation

#### 2.5.1 FastAPI Application
- [ ] Create `backend/app/main.py` with:
  - FastAPI app instance with configuration
  - X-Ray middleware integration
  - CORS middleware setup
  - Structured logging configuration
  - Lifespan management for database initialization

#### 2.5.2 API Endpoints
- [ ] Implement `/health` endpoint:
  - Health check response
  - Database connectivity verification
  - Service status monitoring
- [ ] Implement `/api/query` endpoint:
  - POST endpoint for RAG queries
  - Request validation with Pydantic
  - Async processing
  - Error handling and logging
- [ ] Implement `/api/stats` endpoint:
  - Document count statistics
  - System status information
  - Performance metrics

#### 2.5.3 Container Configuration
- [ ] Create `backend/Dockerfile` with:
  - Multi-stage build for optimization
  - Python 3.11-slim base image
  - Non-root user configuration
  - Health check implementation
  - Proper port exposure

### Phase 2.6: Frontend Implementation

#### 2.6.1 Streamlit Application
- [ ] Create `frontend/requirements.txt` with EXACT versions
- [ ] Create `frontend/app.py` with:
  - Chat interface using st.chat_message
  - Backend API integration with httpx
  - Source document expansion
  - System statistics sidebar
  - Error handling and user feedback

#### 2.6.2 Frontend Container
- [ ] Create `frontend/Dockerfile` with:
  - Streamlit-specific configuration
  - Health check endpoint
  - Proper port configuration
  - Non-root user setup

### Phase 2.7: Testing Implementation

#### 2.7.1 Test Configuration
- [ ] Create `backend/tests/__init__.py`
- [ ] Configure pytest for async testing
- [ ] Set up test database fixtures
- [ ] Mock AWS services for unit testing

#### 2.7.2 RAG Pipeline Tests
- [ ] Create `backend/tests/test_rag.py` with:
  - Embedding generation tests
  - Vector similarity tests
  - End-to-end RAG pipeline tests
  - Error handling tests

#### 2.7.3 API Endpoint Tests
- [ ] Create `backend/tests/test_api.py` with:
  - Health endpoint tests
  - Query endpoint tests
  - Stats endpoint tests
  - Error response validation

### Phase 2.8: CI/CD Configuration

#### 2.8.1 Deployment Specifications
- [ ] Create `backend/appspec.yml` for CodeDeploy
- [ ] Create `frontend/appspec.yml` for CodeDeploy
- [ ] Create `backend/taskdef.json` template
- [ ] Create `frontend/taskdef.json` template

#### 2.8.2 Build Configuration
- [ ] Update `buildspec.yml` with:
  - Backend and frontend Docker builds
  - ECR push operations
  - Task definition generation
  - AppSpec file generation

## Code Quality Standards

### Package Restrictions

**STRICTLY FORBIDDEN**:
- No SQLAlchemy or any ORM
- No additional packages beyond specified list
- No psycopg2 (use psycopg 3 only)
- No external vector databases
- No additional web frameworks

**REQUIRED PATTERNS**:
- Async/await for all I/O operations
- Structured logging with structlog
- Type hints throughout codebase
- Error handling with tenacity retry
- Pydantic models for all data validation

### Performance Requirements

- Connection pooling for database operations
- Async processing for concurrent requests
- Efficient vector indexing with pgvector
- Proper resource cleanup in all components
- Memory-efficient text chunking

### Security Requirements

- Parameterized SQL queries (prevent injection)
- Secrets Manager integration for credentials
- Input validation with Pydantic
- Proper error handling (no information leakage)
- Non-root container execution

## Integration Points

### AWS Services
- Bedrock Runtime for embeddings and generation
- RDS PostgreSQL with pgvector extension
- Secrets Manager for credential management
- X-Ray for distributed tracing
- CloudWatch for structured logging

### Container Orchestration
- ECS Fargate compatibility
- Health check endpoints
- Graceful shutdown handling
- Environment variable configuration

## Validation Criteria

### Functional Testing
- [ ] Health endpoint returns 200 status
- [ ] Query endpoint returns relevant answers
- [ ] Frontend displays chat interface
- [ ] Document ingestion works correctly
- [ ] Vector search returns accurate results

### Performance Testing
- [ ] API response times under 2 seconds
- [ ] Concurrent request handling
- [ ] Memory usage within limits
- [ ] Database query optimization

### Integration Testing
- [ ] ECS Fargate deployment successful
- [ ] Load Balancer routing correct
- [ ] CloudWatch logs structured properly
- [ ] X-Ray traces visible
- [ ] CodeDeploy blue/green deployment works

## Next Steps

After completing Phase 2:

1. Deploy infrastructure using Terraform
2. Build and push Docker images to ECR
3. Deploy applications to ECS Fargate
4. Test end-to-end functionality
5. Validate monitoring and observability
6. Proceed to Phase 3 (CI/CD Pipeline)

## Notes

- This specification is locked for Phase 2 implementation
- Any package changes require formal review and approval
- Focus on simplicity and minimal dependencies
- Prioritize functionality over extensive features
- Maintain production-ready patterns throughout