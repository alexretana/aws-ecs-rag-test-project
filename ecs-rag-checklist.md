# ECS Fargate RAG System - Implementation Checklist

This checklist provides a step-by-step guide for implementing the ECS Fargate RAG System based on the project specification.

---

## Phase 0: Prerequisites and Setup

- [ ] **0.1** Install AWS CLI v2
- [ ] **0.2** Install Terraform
- [ ] **0.3** Install Docker
- [ ] **0.4** Configure AWS credentials (`aws configure`)
- [ ] **0.5** Request Bedrock model access for Titan Embeddings and Llama 3 8B Instruct
- [ ] **0.6** Create project directory structure (run the `mkdir -p` command from spec)
- [ ] **0.7** Create CodeStar connection for GitHub and complete OAuth handshake

---

## Phase 1: Terraform Infrastructure

### Backend Setup (State Management)
- [ ] **1.1** Create `scripts/init-terraform-backend.sh` script
- [ ] **1.2** Run script to create S3 bucket and DynamoDB table for Terraform state

### Core Terraform Files
- [ ] **1.3** Create `terraform/providers.tf` - AWS provider with default tags
- [ ] **1.4** Create `terraform/backend.tf` - S3 backend configuration
- [ ] **1.5** Create `terraform/variables.tf` - Project variables
- [ ] **1.6** Create `terraform/outputs.tf` - ALB DNS, ECR URLs, etc.

### VPC Module
- [ ] **1.7** Create `terraform/modules/vpc/variables.tf`
- [ ] **1.8** Create `terraform/modules/vpc/main.tf`:
  - VPC with DNS support
  - Internet Gateway
  - Public subnets (2 AZs)
  - Private subnets (2 AZs)
  - Public and private route tables
  - Security group for VPC endpoints
- [ ] **1.9** Add VPC endpoints:
  - S3 Gateway endpoint
  - ECR API interface endpoint
  - ECR Docker interface endpoint
  - CloudWatch Logs endpoint
  - Secrets Manager endpoint
  - Bedrock Runtime endpoint
  - X-Ray endpoint
  - ECS, ECS Agent, ECS Telemetry endpoints
- [ ] **1.10** Create `terraform/modules/vpc/outputs.tf`

### Security Module
- [ ] **1.11** Create `terraform/modules/security/variables.tf`
- [ ] **1.12** Create `terraform/modules/security/main.tf`:
  - GuardDuty detector
  - ECS Runtime Monitoring feature
  - Malware protection
- [ ] **1.13** Create `terraform/modules/security/outputs.tf`

### RDS Module
- [ ] **1.14** Create `terraform/modules/rds/variables.tf`
- [ ] **1.15** Create `terraform/modules/rds/main.tf`:
  - Random password generation
  - Secrets Manager secret for DB credentials
  - DB subnet group
  - RDS security group
  - DB parameter group (for pgvector)
  - RDS PostgreSQL 15 instance
  - IAM role for enhanced monitoring
- [ ] **1.16** Create `terraform/modules/rds/outputs.tf`

### Monitoring Module
- [ ] **1.17** Create `terraform/modules/monitoring/variables.tf`
- [ ] **1.18** Create `terraform/modules/monitoring/main.tf`:
  - CloudWatch Log Group
  - X-Ray Sampling Rule
  - CloudWatch Dashboard
  - CloudWatch Alarms (CPU, Memory)
- [ ] **1.19** Create `terraform/modules/monitoring/outputs.tf`

### ALB Module
- [ ] **1.20** Create `terraform/modules/alb/variables.tf`
- [ ] **1.21** Create `terraform/modules/alb/main.tf`:
  - ALB security group
  - Application Load Balancer
  - Backend target groups (Green/Blue)
  - Frontend target groups (Green/Blue)
  - HTTP listener
  - Listener rules for path-based routing
- [ ] **1.22** Create `terraform/modules/alb/outputs.tf`

### ECS Module
- [ ] **1.23** Create `terraform/modules/ecs/variables.tf`
- [ ] **1.24** Create `terraform/modules/ecs/main.tf`:
  - ECR repositories (backend, frontend)
  - ECR lifecycle policies
  - ECS Cluster with Container Insights
  - Capacity provider strategy
  - ECS security group
- [ ] **1.25** Add IAM roles:
  - ECS task execution role (with secrets access)
  - ECS task role (Bedrock, X-Ray, Logs, Secrets permissions)
- [ ] **1.26** Add task definitions and services:
  - Backend task definition (with X-Ray sidecar)
  - Frontend task definition
  - Service discovery namespace
  - Backend ECS service (CODE_DEPLOY controller)
  - Frontend ECS service (CODE_DEPLOY controller)
- [ ] **1.27** Create `terraform/modules/ecs/outputs.tf`

### CodePipeline Module
- [ ] **1.28** Create `terraform/modules/codepipeline/variables.tf`
- [ ] **1.29** Create `terraform/modules/codepipeline/main.tf`:
  - S3 bucket for artifacts
  - CodeBuild project
  - CodeDeploy applications (backend, frontend)
  - CodeDeploy deployment groups (Blue/Green)
  - CodePipeline (Source → Build → Deploy stages)
- [ ] **1.30** Add IAM roles:
  - CodeBuild role (ECR, S3, Logs access)
  - CodeDeploy role
  - CodePipeline role
- [ ] **1.31** Create `terraform/modules/codepipeline/outputs.tf`

### Root Module
- [ ] **1.32** Create `terraform/main.tf` wiring all modules together with proper dependencies

---

## Phase 2: Application Code

### Backend - Core
- [ ] **2.1** Create `backend/requirements.txt` with all Python dependencies
- [ ] **2.2** Create `backend/app/__init__.py`
- [ ] **2.3** Create `backend/app/config.py` - Settings with Secrets Manager integration
- [ ] **2.4** Create `backend/app/models.py` - Pydantic models (Document, QueryRequest, QueryResponse, etc.)

### Backend - Database Layer
- [ ] **2.5** Create `backend/app/db/__init__.py`
- [ ] **2.6** Create `backend/app/db/database.py` - SQLAlchemy engine, session, pgvector extension
- [ ] **2.7** Create `backend/app/db/vector_store.py` - DocumentChunkModel, VectorStore class

### Backend - RAG Components
- [ ] **2.8** Create `backend/app/rag/__init__.py`
- [ ] **2.9** Create `backend/app/rag/embeddings.py` - Bedrock Titan embeddings
- [ ] **2.10** Create `backend/app/rag/retriever.py` - Similarity search
- [ ] **2.11** Create `backend/app/rag/generator.py` - Bedrock Llama 3 generation
- [ ] **2.12** Create `backend/app/rag/pipeline.py` - Full RAG workflow (query, ingest)

### Backend - Seed Data
- [ ] **2.13** Create `backend/app/seed/__init__.py`
- [ ] **2.14** Create `backend/app/seed/data/sample_documents.json` - Sample corpus
- [ ] **2.15** Create `backend/app/seed/corpus.py` - Seed function

### Backend - API & Container
- [ ] **2.16** Create `backend/app/main.py` - FastAPI app with:
  - X-Ray middleware
  - CORS middleware
  - Health endpoint
  - Query endpoint
  - Stats endpoint
  - Lifespan handler for DB init and seeding
- [ ] **2.17** Create `backend/Dockerfile`

### Frontend
- [ ] **2.18** Create `frontend/requirements.txt`
- [ ] **2.19** Create `frontend/app.py` - Streamlit chat interface
- [ ] **2.20** Create `frontend/Dockerfile`

### Backend Tests
- [ ] **2.21** Create `backend/tests/__init__.py`
- [ ] **2.22** Create `backend/tests/test_rag.py`
- [ ] **2.23** Create `backend/tests/test_api.py`

---

## Phase 3: CI/CD Configuration

- [ ] **3.1** Create `buildspec.yml` for CodeBuild:
  - ECR login
  - Docker builds for backend and frontend
  - Image push to ECR
  - ECR scan results check
  - Generate task definition files
  - Generate appspec files
  - Generate imageDetail.json files
- [ ] **3.2** Create `backend/appspec.yml` for CodeDeploy
- [ ] **3.3** Create `frontend/appspec.yml` for CodeDeploy
- [ ] **3.4** Create `backend/taskdef.json` template
- [ ] **3.5** Create `frontend/taskdef.json` template

---

## Phase 4: Deployment

### Scripts
- [ ] **4.1** Create `scripts/deploy.sh` - Terraform deployment script
- [ ] **4.2** Create `scripts/seed-database.sh` (if needed separately)
- [ ] **4.3** Create `scripts/initial-push.sh` for first Docker images

### Deploy Infrastructure
- [ ] **4.4** Run `init-terraform-backend.sh`
- [ ] **4.5** Run `terraform init`
- [ ] **4.6** Run `terraform plan`
- [ ] **4.7** Run `terraform apply`
- [ ] **4.8** Build and push initial Docker images to ECR

---

## Phase 5: Testing and Validation

### Functional Tests
- [ ] **5.1** Verify ALB health endpoint responds (`curl http://$ALB_DNS/health`)
- [ ] **5.2** Test RAG query endpoint (`POST /api/query`)
- [ ] **5.3** Access Streamlit UI in browser

### Monitoring Verification
- [ ] **5.4** Verify CloudWatch logs are streaming
- [ ] **5.5** Verify X-Ray traces are appearing
- [ ] **5.6** Check CloudWatch dashboard

### Security Verification
- [ ] **5.7** Verify ECR scan results (check for critical vulnerabilities)
- [ ] **5.8** Verify GuardDuty ECS Runtime Monitoring is enabled

### CI/CD Verification
- [ ] **5.9** Test Blue/Green deployment by pushing code change

---

## Phase 6: Documentation

- [ ] **6.1** Create/update `README.md` with:
  - Project overview
  - Architecture diagram
  - Prerequisites
  - Setup instructions
  - Usage guide
  - Troubleshooting
  - Cost estimation
  - Cleanup instructions

---

## Quick Reference

### Key Commands

```bash
# Initialize Terraform backend
./scripts/init-terraform-backend.sh

# Deploy infrastructure
cd terraform && terraform init && terraform apply

# Push initial images
./scripts/initial-push.sh

# Test health
curl http://$ALB_DNS/health

# Test RAG query
curl -X POST http://$ALB_DNS/api/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What is machine learning?", "top_k": 3}'

# View logs
aws logs tail /ecs/ecs-rag-dev --follow

# Cleanup
terraform destroy
```

### Estimated Timeline

| Phase | Duration |
|-------|----------|
| Phase 0: Prerequisites | 1-2 hours |
| Phase 1: Terraform | 4-6 hours |
| Phase 2: Application Code | 3-4 hours |
| Phase 3: CI/CD Config | 1-2 hours |
| Phase 4: Deployment | 1-2 hours |
| Phase 5: Testing | 1-2 hours |
| Phase 6: Documentation | 1 hour |
| **Total** | **12-19 hours** |

---

*Generated from ecs-rag-project-spec.MD*