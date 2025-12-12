# Local Testing Checklist

Use this checklist to verify your RAG application is working correctly before deploying to AWS.

## Prerequisites Checklist

- [ ] Docker and Docker Compose installed
- [ ] Git repository cloned locally
- [ ] AWS CLI configured (if using real AWS services)
- [ ] Sufficient disk space for Docker images and data

## Setup Verification

### Docker Compose Configuration
- [ ] docker-compose.yml file created in project root
- [ ] PostgreSQL service configured with pgvector image
- [ ] Backend service configured with correct environment variables
- [ ] Frontend service configured with correct backend URL
- [ ] Proper port mappings (5432, 8000, 8501)
- [ ] Health checks configured for PostgreSQL
- [ ] Service dependencies properly set

### Backend Configuration
- [ ] config.py updated to use environment variables
- [ ] Mock AWS services implemented (if using local testing)
- [ ] Database connection settings configured
- [ ] AWS credentials settings configured
- [ ] Bedrock model IDs configured

### Mock Services (if using local testing without AWS)
- [ ] Mock Bedrock Runtime service created
- [ ] Embedding generation mock implemented
- [ ] Text generation mock implemented
- [ ] Contextual responses based on sample documents
- [ ] Deterministic embeddings for consistent testing

## Startup Verification

### Service Health Checks
- [ ] PostgreSQL container starts successfully
- [ ] PostgreSQL health check passes
- [ ] Backend container starts successfully
- [ ] Frontend container starts successfully
- [ ] All containers are running: `docker-compose ps`

### Database Initialization
- [ ] pgvector extension enabled
- [ ] document_chunks table created
- [ ] Vector indexes created
- [ ] Sample documents seeded successfully
- [ ] Database connection working from backend

## Functional Testing Checklist

### Backend API Tests

#### Health Endpoint
- [ ] GET /health returns 200 status code
- [ ] Response contains "status": "healthy"
- [ ] Response includes timestamp
- [ ] Response includes version "1.0.0"

#### Query Endpoint
- [ ] POST /api/query accepts valid requests
- [ ] Returns relevant answers for sample questions:
  - [ ] "What is machine learning?"
  - [ ] "Explain cloud computing"
  - [ ] "What is Kubernetes?"
  - [ ] "How does RAG work?"
- [ ] Response includes answer field
- [ ] Response includes sources array
- [ ] Sources include similarity scores
- [ ] Sources include content snippets
- [ ] Handles empty queries gracefully
- [ ] Handles invalid requests with proper error codes

#### Stats Endpoint
- [ ] GET /api/stats returns 200 status code
- [ ] Response includes chunk_count
- [ ] Response includes timestamp
- [ ] Chunk count matches seeded documents

#### API Documentation
- [ ] GET /api/docs returns documentation links
- [ ] OpenAPI spec accessible at /openapi.json
- [ ] Swagger UI accessible at /docs
- [ ] ReDoc accessible at /redoc

### Frontend Tests

#### Basic Functionality
- [ ] Frontend loads at http://localhost:8501
- [ ] Page title displays correctly
- [ ] Chat interface appears
- [ ] System info sidebar displays
- [ ] Document count shows correct number

#### Chat Interaction
- [ ] Can type questions in chat input
- [ ] Questions appear in chat history
- [ ] Assistant responses appear
- [ ] Sources expand/collapse correctly
- [ ] Similarity scores displayed
- [ ] Clear chat button works

#### Integration with Backend
- [ ] Frontend successfully connects to backend
- [ ] Questions are sent to backend API
- [ ] Responses are displayed correctly
- [ ] Error messages displayed when backend unavailable
- [ ] Stats fetched and displayed in sidebar

## Data Verification

### Sample Documents
- [ ] All 6 sample documents loaded
- [ ] Documents properly chunked
- [ ] Embeddings generated for all chunks
- [ ] Vector similarity search returns relevant results
- [ ] Metadata preserved correctly

### Search Quality
- [ ] Queries about machine learning return ML documents
- [ ] Queries about cloud computing return cloud documents
- [ ] Queries about Kubernetes return DevOps documents
- [ ] Queries about RAG return AI/ML documents
- [ ] Similarity scores are reasonable (0.7+ for good matches)

## Error Handling Tests

### Backend Error Handling
- [ ] Invalid JSON requests return 422
- [ ] Missing required fields return appropriate errors
- [ ] Database connection failures handled gracefully
- [ ] AWS service failures handled gracefully
- [ ] Structured logging works correctly

### Frontend Error Handling
- [ ] Network errors displayed to user
- [ ] Backend unavailable shows appropriate message
- [ ] Invalid input handled gracefully
- [ ] Page refresh maintains state correctly

## Performance Tests

### Response Times
- [ ] Health endpoint responds in <100ms
- [ ] Query endpoint responds in <5 seconds
- [ ] Stats endpoint responds in <500ms
- [ ] Frontend loads in <3 seconds

### Resource Usage
- [ ] Memory usage stable during testing
- [ ] CPU usage reasonable during queries
- [ ] Database queries efficient
- [ ] No memory leaks detected

## Security Tests

### CORS Configuration
- [ ] CORS headers present in API responses
- [ ] Appropriate origins allowed (configured for production)
- [ ] Appropriate methods allowed
- [ ] Appropriate headers allowed

### Input Validation
- [ ] SQL injection attempts blocked
- [ ] XSS attempts blocked
- [ ] Input size limits enforced
- [ ] Special characters handled correctly

## Integration Tests

### End-to-End Workflow
- [ ] Complete question-answer cycle works
- [ ] Document ingestion works (if implemented)
- [ ] Vector search and generation pipeline works
- [ ] Error recovery works correctly

### Docker Integration
- [ ] Volume mounts work correctly
- [ ] Port forwarding works correctly
- [ ] Container networking works correctly
- [ ] Environment variables passed correctly

## Cleanup Tests

### Container Cleanup
- [ ] `docker-compose down` removes all containers
- [ ] `docker-compose down -v` removes volumes (optional)
- [ ] No orphaned containers left running
- [ ] Ports released correctly

## Final Verification Before Deployment

### Code Quality
- [ ] No obvious bugs or issues found
- [ ] Error messages are user-friendly
- [ ] Logging is comprehensive but not excessive
- [ ] Configuration is flexible

### Documentation
- [ ] README updated with local testing instructions
- [ ] Configuration documented
- [ ] Dependencies documented
- [ ] Troubleshooting guide created

### Deployment Readiness
- [ ] All tests pass consistently
- [ ] Application works with real AWS services (if applicable)
- [ ] Environment variables documented for production
- [ ] Docker images build correctly

## Troubleshooting Quick Reference

### Common Issues and Solutions

1. **PostgreSQL Connection Failed**
   - Check if PostgreSQL container is running
   - Verify database credentials in environment
   - Check if pgvector extension is enabled

2. **Backend Won't Start**
   - Check backend logs: `docker-compose logs backend`
   - Verify all environment variables are set
   - Check if database is accessible

3. **Frontend Can't Connect to Backend**
   - Verify backend is running and healthy
   - Check BACKEND_URL environment variable
   - Verify port mapping in docker-compose.yml

4. **No Search Results**
   - Check if database is seeded: `curl http://localhost:8000/api/stats`
   - Verify embeddings are being generated
   - Check vector similarity search logic

5. **Mock Services Not Working**
   - Verify mock service files are correctly placed
   - Check import statements in backend code
   - Verify environment variable for local testing

## Test Commands Reference

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs [service-name]

# Test backend health
curl http://localhost:8000/health

# Test query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 3}'

# Test stats endpoint
curl http://localhost:8000/api/stats

# Stop all services
docker-compose down

# Remove volumes (clean start)
docker-compose down -v
```

## Completion Criteria

Consider your local testing complete when:

1. All services start successfully
2. All health checks pass
3. Sample queries return relevant answers
4. Frontend displays responses correctly
5. Error handling works as expected
6. Performance is acceptable
7. No critical errors in logs
8. All checklist items are marked as complete

Once you've completed this checklist, you should have confidence that your RAG application will work correctly when deployed to AWS ECS.