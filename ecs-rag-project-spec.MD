# ECS Fargate RAG System - Complete Project Specification

## Project Overview

This document provides complete, executable instructions for building a production-style RAG (Retrieval-Augmented Generation) system on AWS ECS Fargate. An agentic model should be able to execute this end-to-end.

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                    VPC                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Public Subnet (2 AZs)                           ││
│  │  ┌─────────────────┐                                                    ││
│  │  │ Internet Gateway│                                                    ││
│  │  └────────┬────────┘                                                    ││
│  │           │                                                             ││
│  │  ┌────────▼────────┐                                                    ││
│  │  │      ALB        │                                                    ││
│  │  └────────┬────────┘                                                    ││
│  └───────────┼─────────────────────────────────────────────────────────────┘│
│              │                                                               │
│  ┌───────────▼─────────────────────────────────────────────────────────────┐│
│  │                        Private Subnet (2 AZs)                           ││
│  │                                                                         ││
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              ││
│  │  │  RAG Backend │    │  Streamlit   │    │   RDS        │              ││
│  │  │  (Fargate)   │    │  (Fargate)   │    │  PostgreSQL  │              ││
│  │  │              │    │              │    │  + pgvector  │              ││
│  │  └──────┬───────┘    └──────────────┘    └──────────────┘              ││
│  │         │                                                               ││
│  │  ┌──────▼───────────────────────────────────────────────┐              ││
│  │  │              VPC Endpoints                            │              ││
│  │  │  • bedrock-runtime  • ecr.api  • ecr.dkr             │              ││
│  │  │  • logs             • s3       • xray                 │              ││
│  │  │  • secretsmanager                                     │              ││
│  │  └───────────────────────────────────────────────────────┘              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| IaC | Terraform (S3 backend) |
| Container Orchestration | ECS Fargate |
| Container Registry | ECR (with native scanning) |
| Load Balancer | Application Load Balancer |
| Backend | Python (FastAPI) |
| Frontend | Streamlit |
| Vector Database | RDS PostgreSQL + pgvector |
| Embeddings | Bedrock Titan Embeddings |
| LLM | Bedrock Llama 3 8B Instruct |
| CI/CD | CodePipeline + CodeDeploy (Blue/Green) |
| Monitoring | CloudWatch Logs, Container Insights, X-Ray |
| Security | ECR Scanning, GuardDuty ECS Runtime Monitoring |

---

## Prerequisites

### Required Tools

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installations
aws --version
terraform --version
docker --version
```

### AWS Account Setup

```bash
# Configure AWS credentials
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Default region (e.g., us-east-1), output format (json)

# Verify Bedrock model access - request access in AWS Console first:
# Console → Bedrock → Model access → Request access for:
#   - Titan Embeddings G1 - Text
#   - Meta Llama 3 8B Instruct

# Verify access
aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'titan-embed') || contains(modelId, 'llama3-8b')]"
```

---

## Directory Structure

Create the following project structure:

```
ecs-rag-project/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── backend.tf
│   ├── modules/
│   │   ├── vpc/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── ecs/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── rds/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── alb/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── codepipeline/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── monitoring/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── security/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── embeddings.py
│   │   │   ├── retriever.py
│   │   │   ├── generator.py
│   │   │   └── pipeline.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   └── vector_store.py
│   │   └── seed/
│   │       ├── __init__.py
│   │       ├── corpus.py
│   │       └── data/
│   │           └── sample_documents.json
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_rag.py
│   │   └── test_api.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── appspec.yml
│   └── taskdef.json
├── frontend/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── appspec.yml
│   └── taskdef.json
├── scripts/
│   ├── init-terraform-backend.sh
│   ├── deploy.sh
│   └── seed-database.sh
├── buildspec.yml
└── README.md
```

**Command to create structure:**

```bash
mkdir -p ecs-rag-project/{terraform/modules/{vpc,ecs,rds,alb,codepipeline,monitoring,security},backend/{app/{rag,db,seed/data},tests},frontend,scripts}
touch ecs-rag-project/terraform/{main.tf,variables.tf,outputs.tf,providers.tf,backend.tf}
touch ecs-rag-project/terraform/modules/vpc/{main.tf,variables.tf,outputs.tf}
touch ecs-rag-project/terraform/modules/ecs/{main.tf,variables.tf,outputs.tf}
touch ecs-rag-project/terraform/modules/rds/{main.tf,variables.tf,outputs.tf}
touch ecs-rag-project/terraform/modules/alb/{main.tf,variables.tf,outputs.tf}
touch ecs-rag-project/terraform/modules/codepipeline/{main.tf,variables.tf,outputs.tf}
touch ecs-rag-project/terraform/modules/monitoring/{main.tf,variables.tf,outputs.tf}
touch ecs-rag-project/terraform/modules/security/{main.tf,variables.tf,outputs.tf}
touch ecs-rag-project/backend/app/{__init__.py,main.py,config.py,models.py}
touch ecs-rag-project/backend/app/rag/{__init__.py,embeddings.py,retriever.py,generator.py,pipeline.py}
touch ecs-rag-project/backend/app/db/{__init__.py,database.py,vector_store.py}
touch ecs-rag-project/backend/app/seed/{__init__.py,corpus.py}
touch ecs-rag-project/backend/app/seed/data/sample_documents.json
touch ecs-rag-project/backend/tests/{__init__.py,test_rag.py,test_api.py}
touch ecs-rag-project/backend/{Dockerfile,requirements.txt,appspec.yml,taskdef.json}
touch ecs-rag-project/frontend/{app.py,Dockerfile,requirements.txt,appspec.yml,taskdef.json}
touch ecs-rag-project/scripts/{init-terraform-backend.sh,deploy.sh,seed-database.sh}
touch ecs-rag-project/{buildspec.yml,README.md}
cd ecs-rag-project
```

---

## Phase 1: Terraform Infrastructure

### 1.1 Initialize Terraform Backend

**File: `scripts/init-terraform-backend.sh`**

```bash
#!/bin/bash
set -e

PROJECT_NAME="ecs-rag-project"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create S3 bucket for Terraform state
BUCKET_NAME="${PROJECT_NAME}-tfstate-${ACCOUNT_ID}"
aws s3api create-bucket \
    --bucket ${BUCKET_NAME} \
    --region ${REGION}

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket ${BUCKET_NAME} \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket ${BUCKET_NAME} \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "aws:kms"
                }
            }
        ]
    }'

# Block public access
aws s3api put-public-access-block \
    --bucket ${BUCKET_NAME} \
    --public-access-block-configuration '{
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }'

# Create DynamoDB table for state locking
aws dynamodb create-table \
    --table-name ${PROJECT_NAME}-tflock \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ${REGION}

echo "Terraform backend created:"
echo "  S3 Bucket: ${BUCKET_NAME}"
echo "  DynamoDB Table: ${PROJECT_NAME}-tflock"
```

Run: `chmod +x scripts/init-terraform-backend.sh && ./scripts/init-terraform-backend.sh`

### 1.2 Terraform Provider Configuration

**File: `terraform/providers.tf`**

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

**File: `terraform/backend.tf`**

```hcl
terraform {
  backend "s3" {
    bucket         = "ecs-rag-project-tfstate-ACCOUNT_ID"  # Replace ACCOUNT_ID
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ecs-rag-project-tflock"
    encrypt        = true
  }
}
```

**File: `terraform/variables.tf`**

```hcl
variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ecs-rag"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "ragadmin"
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "ragdb"
}

variable "github_repo" {
  description = "GitHub repository for CodePipeline (format: owner/repo)"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch to track"
  type        = string
  default     = "main"
}

variable "codestar_connection_arn" {
  description = "ARN of CodeStar connection for GitHub"
  type        = string
}
```

**File: `terraform/outputs.tf`**

```hcl
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "backend_ecr_repository_url" {
  description = "ECR repository URL for backend"
  value       = module.ecs.backend_ecr_repository_url
}

output "frontend_ecr_repository_url" {
  description = "ECR repository URL for frontend"
  value       = module.ecs.frontend_ecr_repository_url
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = module.monitoring.log_group_name
}
```

**File: `terraform/main.tf`**

```hcl
data "aws_caller_identity" "current" {}

module "vpc" {
  source = "./modules/vpc"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  aws_region         = var.aws_region
}

module "security" {
  source = "./modules/security"

  project_name = var.project_name
  environment  = var.environment
}

module "rds" {
  source = "./modules/rds"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  db_username         = var.db_username
  db_name             = var.db_name
  ecs_security_group_id = module.ecs.ecs_security_group_id

  depends_on = [module.vpc]
}

module "alb" {
  source = "./modules/alb"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids

  depends_on = [module.vpc]
}

module "monitoring" {
  source = "./modules/monitoring"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
}

module "ecs" {
  source = "./modules/ecs"

  project_name              = var.project_name
  environment               = var.environment
  aws_region                = var.aws_region
  vpc_id                    = module.vpc.vpc_id
  private_subnet_ids        = module.vpc.private_subnet_ids
  alb_security_group_id     = module.alb.security_group_id
  backend_target_group_arn  = module.alb.backend_target_group_arn
  frontend_target_group_arn = module.alb.frontend_target_group_arn
  db_secret_arn             = module.rds.secret_arn
  log_group_name            = module.monitoring.log_group_name
  xray_sampling_rule_name   = module.monitoring.xray_sampling_rule_name

  depends_on = [module.vpc, module.alb, module.rds, module.monitoring]
}

module "codepipeline" {
  source = "./modules/codepipeline"

  project_name                  = var.project_name
  environment                   = var.environment
  aws_region                    = var.aws_region
  account_id                    = data.aws_caller_identity.current.account_id
  github_repo                   = var.github_repo
  github_branch                 = var.github_branch
  codestar_connection_arn       = var.codestar_connection_arn
  backend_ecr_repository_url    = module.ecs.backend_ecr_repository_url
  frontend_ecr_repository_url   = module.ecs.frontend_ecr_repository_url
  ecs_cluster_name              = module.ecs.cluster_name
  backend_service_name          = module.ecs.backend_service_name
  frontend_service_name         = module.ecs.frontend_service_name
  backend_target_group_name     = module.alb.backend_target_group_name
  frontend_target_group_name    = module.alb.frontend_target_group_name
  backend_target_group_blue_name  = module.alb.backend_target_group_blue_name
  frontend_target_group_blue_name = module.alb.frontend_target_group_blue_name
  alb_listener_arn              = module.alb.listener_arn
  backend_listener_rule_arn     = module.alb.backend_listener_rule_arn
  frontend_listener_rule_arn    = module.alb.frontend_listener_rule_arn

  depends_on = [module.ecs, module.alb]
}
```

### 1.3 VPC Module

**File: `terraform/modules/vpc/variables.tf`**

```hcl
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "availability_zones" {
  type = list(string)
}

variable "aws_region" {
  type = string
}
```

**File: `terraform/modules/vpc/main.tf`**

```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-public-${var.availability_zones[count.index]}"
    Type = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-${var.environment}-private-${var.availability_zones[count.index]}"
    Type = "private"
  }
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private Route Table (no NAT - using VPC endpoints)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security Group for VPC Endpoints
resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.project_name}-${var.environment}-vpce-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "HTTPS from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-vpce-sg"
  }
}

# VPC Endpoints for AWS Services

# S3 Gateway Endpoint (free)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]

  tags = {
    Name = "${var.project_name}-${var.environment}-s3-endpoint"
  }
}

# ECR API Endpoint
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-ecr-api-endpoint"
  }
}

# ECR Docker Endpoint
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-ecr-dkr-endpoint"
  }
}

# CloudWatch Logs Endpoint
resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-logs-endpoint"
  }
}

# Secrets Manager Endpoint
resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-secretsmanager-endpoint"
  }
}

# Bedrock Runtime Endpoint
resource "aws_vpc_endpoint" "bedrock_runtime" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-bedrock-runtime-endpoint"
  }
}

# X-Ray Endpoint
resource "aws_vpc_endpoint" "xray" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.xray"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-xray-endpoint"
  }
}

# ECS Endpoints (required for Fargate)
resource "aws_vpc_endpoint" "ecs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-endpoint"
  }
}

resource "aws_vpc_endpoint" "ecs_agent" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecs-agent"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-agent-endpoint"
  }
}

resource "aws_vpc_endpoint" "ecs_telemetry" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecs-telemetry"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-telemetry-endpoint"
  }
}
```

**File: `terraform/modules/vpc/outputs.tf`**

```hcl
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "vpc_endpoints_security_group_id" {
  value = aws_security_group.vpc_endpoints.id
}
```

### 1.4 RDS Module

**File: `terraform/modules/rds/variables.tf`**

```hcl
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_name" {
  type = string
}

variable "ecs_security_group_id" {
  type = string
}
```

**File: `terraform/modules/rds/main.tf`**

```hcl
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.project_name}-${var.environment}-db-credentials"
  recovery_window_in_days = 0  # For dev - set to 7+ for production

  tags = {
    Name = "${var.project_name}-${var.environment}-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    dbname   = var.db_name
    host     = aws_db_instance.main.address
    port     = 5432
  })
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
    description     = "PostgreSQL from ECS tasks"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  }
}

resource "aws_db_parameter_group" "main" {
  name   = "${var.project_name}-${var.environment}-pg-params"
  family = "postgres15"

  # Enable pgvector extension
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-pg-params"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-${var.environment}-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"  # Smallest for dev

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.main.name

  publicly_accessible    = false
  multi_az               = false  # Single AZ for dev
  skip_final_snapshot    = true   # For dev - set false for production
  deletion_protection    = false  # For dev - set true for production

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-db"
  }
}

# IAM role for enhanced monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project_name}-${var.environment}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}
```

**File: `terraform/modules/rds/outputs.tf`**

```hcl
output "endpoint" {
  value     = aws_db_instance.main.address
  sensitive = true
}

output "secret_arn" {
  value = aws_secretsmanager_secret.db_credentials.arn
}

output "security_group_id" {
  value = aws_security_group.rds.id
}
```

### 1.5 ALB Module

**File: `terraform/modules/alb/variables.tf`**

```hcl
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}
```

**File: `terraform/modules/alb/main.tf`**

```hcl
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP from internet"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from internet"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  }
}

resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false  # For dev

  tags = {
    Name = "${var.project_name}-${var.environment}-alb"
  }
}

# Backend Target Groups (Green/Blue for Blue-Green deployment)
resource "aws_lb_target_group" "backend_green" {
  name        = "${var.project_name}-${var.environment}-be-green"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-tg-green"
  }
}

resource "aws_lb_target_group" "backend_blue" {
  name        = "${var.project_name}-${var.environment}-be-blue"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-tg-blue"
  }
}

# Frontend Target Groups (Green/Blue)
resource "aws_lb_target_group" "frontend_green" {
  name        = "${var.project_name}-${var.environment}-fe-green"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/_stcore/health"
    matcher             = "200"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-frontend-tg-green"
  }
}

resource "aws_lb_target_group" "frontend_blue" {
  name        = "${var.project_name}-${var.environment}-fe-blue"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/_stcore/health"
    matcher             = "200"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-frontend-tg-blue"
  }
}

# HTTP Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_green.arn
  }
}

# Listener Rules for path-based routing
resource "aws_lb_listener_rule" "backend" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_green.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/health", "/docs", "/openapi.json"]
    }
  }
}

resource "aws_lb_listener_rule" "frontend" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_green.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}
```

**File: `terraform/modules/alb/outputs.tf`**

```hcl
output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "alb_arn" {
  value = aws_lb.main.arn
}

output "security_group_id" {
  value = aws_security_group.alb.id
}

output "backend_target_group_arn" {
  value = aws_lb_target_group.backend_green.arn
}

output "frontend_target_group_arn" {
  value = aws_lb_target_group.frontend_green.arn
}

output "backend_target_group_name" {
  value = aws_lb_target_group.backend_green.name
}

output "frontend_target_group_name" {
  value = aws_lb_target_group.frontend_green.name
}

output "backend_target_group_blue_name" {
  value = aws_lb_target_group.backend_blue.name
}

output "frontend_target_group_blue_name" {
  value = aws_lb_target_group.frontend_blue.name
}

output "listener_arn" {
  value = aws_lb_listener.http.arn
}

output "backend_listener_rule_arn" {
  value = aws_lb_listener_rule.backend.arn
}

output "frontend_listener_rule_arn" {
  value = aws_lb_listener_rule.frontend.arn
}
```

### 1.6 ECS Module

**File: `terraform/modules/ecs/variables.tf`**

```hcl
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "backend_target_group_arn" {
  type = string
}

variable "frontend_target_group_arn" {
  type = string
}

variable "db_secret_arn" {
  type = string
}

variable "log_group_name" {
  type = string
}

variable "xray_sampling_rule_name" {
  type = string
}
```

**File: `terraform/modules/ecs/main.tf`**

```hcl
# ECR Repositories
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-${var.environment}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true  # Enable ECR native scanning
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend"
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${var.project_name}-${var.environment}-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-frontend"
  }
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = aws_ecr_repository.frontend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cluster"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# ECS Security Group
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
    description     = "Backend from ALB"
  }

  ingress {
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
    description     = "Frontend (Streamlit) from ALB"
  }

  # Allow inter-service communication
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    self        = true
    description = "Backend from other ECS tasks"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  }
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-${var.environment}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "${var.project_name}-${var.environment}-ecs-secrets"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [var.db_secret_arn]
      }
    ]
  })
}

# ECS Task Role (for application code)
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${var.environment}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "ecs_task_bedrock" {
  name = "${var.project_name}-${var.environment}-bedrock"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v1",
          "arn:aws:bedrock:*::foundation-model/meta.llama3-8b-instruct-v1:0"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "ecs_task_xray" {
  name = "${var.project_name}-${var.environment}-xray"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "xray:GetSamplingStatisticSummaries"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "ecs_task_logs" {
  name = "${var.project_name}-${var.environment}-logs"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "ecs_task_secrets" {
  name = "${var.project_name}-${var.environment}-task-secrets"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [var.db_secret_arn]
      }
    ]
  })
}

# Backend Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-${var.environment}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${aws_ecr_repository.backend.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "AWS_XRAY_DAEMON_ADDRESS"
          value = "localhost:2000"
        }
      ]

      secrets = [
        {
          name      = "DB_SECRET"
          valueFrom = var.db_secret_arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group_name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    },
    {
      name  = "xray-daemon"
      image = "amazon/aws-xray-daemon:latest"
      
      portMappings = [
        {
          containerPort = 2000
          hostPort      = 2000
          protocol      = "udp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group_name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "xray"
        }
      }

      cpu    = 32
      memory = 256
    }
  ])

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-task"
  }
}

# Frontend Task Definition
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project_name}-${var.environment}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "frontend"
      image = "${aws_ecr_repository.frontend.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "BACKEND_URL"
          value = "http://localhost:8000"  # Will be updated via service discovery
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group_name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "frontend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-${var.environment}-frontend-task"
  }
}

# Service Discovery Namespace
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${var.project_name}.local"
  description = "Private DNS namespace for ECS services"
  vpc         = var.vpc_id
}

resource "aws_service_discovery_service" "backend" {
  name = "backend"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

# Backend ECS Service
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-${var.environment}-backend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  deployment_controller {
    type = "CODE_DEPLOY"
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.backend_target_group_arn
    container_name   = "backend"
    container_port   = 8000
  }

  service_registries {
    registry_arn = aws_service_discovery_service.backend.arn
  }

  lifecycle {
    ignore_changes = [task_definition, load_balancer]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-service"
  }
}

# Frontend ECS Service
resource "aws_ecs_service" "frontend" {
  name            = "${var.project_name}-${var.environment}-frontend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  deployment_controller {
    type = "CODE_DEPLOY"
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.frontend_target_group_arn
    container_name   = "frontend"
    container_port   = 8501
  }

  lifecycle {
    ignore_changes = [task_definition, load_balancer]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-frontend-service"
  }
}
```

**File: `terraform/modules/ecs/outputs.tf`**

```hcl
output "cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  value = aws_ecs_cluster.main.arn
}

output "backend_service_name" {
  value = aws_ecs_service.backend.name
}

output "frontend_service_name" {
  value = aws_ecs_service.frontend.name
}

output "backend_ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_repository_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "ecs_security_group_id" {
  value = aws_security_group.ecs_tasks.id
}

output "task_execution_role_arn" {
  value = aws_iam_role.ecs_task_execution.arn
}

output "task_role_arn" {
  value = aws_iam_role.ecs_task.arn
}
```

### 1.7 Monitoring Module

**File: `terraform/modules/monitoring/variables.tf`**

```hcl
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}
```

**File: `terraform/modules/monitoring/main.tf`**

```hcl
# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${var.project_name}-${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-${var.environment}-logs"
  }
}

# X-Ray Sampling Rule
resource "aws_xray_sampling_rule" "main" {
  rule_name      = "${var.project_name}-${var.environment}-sampling"
  priority       = 1000
  version        = 1
  reservoir_size = 5
  fixed_rate     = 0.1  # 10% sampling
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"

  attributes = {}
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "ECS Service CPU Utilization"
          region = var.aws_region
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "${var.project_name}-${var.environment}-backend-service", "ClusterName", "${var.project_name}-${var.environment}-cluster"],
            ["AWS/ECS", "CPUUtilization", "ServiceName", "${var.project_name}-${var.environment}-frontend-service", "ClusterName", "${var.project_name}-${var.environment}-cluster"]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "ECS Service Memory Utilization"
          region = var.aws_region
          metrics = [
            ["AWS/ECS", "MemoryUtilization", "ServiceName", "${var.project_name}-${var.environment}-backend-service", "ClusterName", "${var.project_name}-${var.environment}-cluster"],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", "${var.project_name}-${var.environment}-frontend-service", "ClusterName", "${var.project_name}-${var.environment}-cluster"]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "ALB Request Count"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "${var.project_name}-${var.environment}-alb"]
          ]
          period = 60
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "ALB Response Times"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "${var.project_name}-${var.environment}-alb"]
          ]
          period = 60
          stat   = "Average"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 24
        height = 6
        properties = {
          title  = "Application Logs"
          region = var.aws_region
          query  = "SOURCE '/ecs/${var.project_name}-${var.environment}' | fields @timestamp, @message | sort @timestamp desc | limit 100"
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "backend_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-backend-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Backend CPU utilization is too high"

  dimensions = {
    ClusterName = "${var.project_name}-${var.environment}-cluster"
    ServiceName = "${var.project_name}-${var.environment}-backend-service"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-cpu-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "backend_memory_high" {
  alarm_name          = "${var.project_name}-${var.environment}-backend-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Backend memory utilization is too high"

  dimensions = {
    ClusterName = "${var.project_name}-${var.environment}-cluster"
    ServiceName = "${var.project_name}-${var.environment}-backend-service"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-memory-alarm"
  }
}
```

**File: `terraform/modules/monitoring/outputs.tf`**

```hcl
output "log_group_name" {
  value = aws_cloudwatch_log_group.main.name
}

output "log_group_arn" {
  value = aws_cloudwatch_log_group.main.arn
}

output "xray_sampling_rule_name" {
  value = aws_xray_sampling_rule.main.rule_name
}

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.main.dashboard_name
}
```

### 1.8 Security Module (GuardDuty)

**File: `terraform/modules/security/variables.tf`**

```hcl
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}
```

**File: `terraform/modules/security/main.tf`**

```hcl
# GuardDuty Detector
resource "aws_guardduty_detector" "main" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = false  # Not using EKS
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-guardduty"
  }
}

# Enable ECS Runtime Monitoring
resource "aws_guardduty_detector_feature" "ecs_runtime_monitoring" {
  detector_id = aws_guardduty_detector.main.id
  name        = "ECS_RUNTIME_MONITORING"
  status      = "ENABLED"

  additional_configuration {
    name   = "ECS_FARGATE_AGENT_MANAGEMENT"
    status = "ENABLED"
  }
}
```

**File: `terraform/modules/security/outputs.tf`**

```hcl
output "guardduty_detector_id" {
  value = aws_guardduty_detector.main.id
}
```

### 1.9 CodePipeline Module

**File: `terraform/modules/codepipeline/variables.tf`**

```hcl
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "account_id" {
  type = string
}

variable "github_repo" {
  type = string
}

variable "github_branch" {
  type = string
}

variable "codestar_connection_arn" {
  type = string
}

variable "backend_ecr_repository_url" {
  type = string
}

variable "frontend_ecr_repository_url" {
  type = string
}

variable "ecs_cluster_name" {
  type = string
}

variable "backend_service_name" {
  type = string
}

variable "frontend_service_name" {
  type = string
}

variable "backend_target_group_name" {
  type = string
}

variable "frontend_target_group_name" {
  type = string
}

variable "backend_target_group_blue_name" {
  type = string
}

variable "frontend_target_group_blue_name" {
  type = string
}

variable "alb_listener_arn" {
  type = string
}

variable "backend_listener_rule_arn" {
  type = string
}

variable "frontend_listener_rule_arn" {
  type = string
}
```

**File: `terraform/modules/codepipeline/main.tf`**

```hcl
# S3 Bucket for CodePipeline artifacts
resource "aws_s3_bucket" "codepipeline" {
  bucket = "${var.project_name}-${var.environment}-codepipeline-${var.account_id}"

  tags = {
    Name = "${var.project_name}-${var.environment}-codepipeline"
  }
}

resource "aws_s3_bucket_versioning" "codepipeline" {
  bucket = aws_s3_bucket.codepipeline.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "codepipeline" {
  bucket = aws_s3_bucket.codepipeline.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# CodeBuild IAM Role
resource "aws_iam_role" "codebuild" {
  name = "${var.project_name}-${var.environment}-codebuild"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "codebuild" {
  name = "${var.project_name}-${var.environment}-codebuild-policy"
  role = aws_iam_role.codebuild.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.codepipeline.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:DescribeImageScanFindings"
        ]
        Resource = [
          "arn:aws:ecr:${var.aws_region}:${var.account_id}:repository/${var.project_name}-${var.environment}-backend",
          "arn:aws:ecr:${var.aws_region}:${var.account_id}:repository/${var.project_name}-${var.environment}-frontend"
        ]
      }
    ]
  })
}

# CodeBuild Project
resource "aws_codebuild_project" "main" {
  name         = "${var.project_name}-${var.environment}-build"
  description  = "Build project for ${var.project_name}"
  service_role = aws_iam_role.codebuild.arn

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode             = true  # Required for Docker builds

    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = var.account_id
    }

    environment_variable {
      name  = "BACKEND_ECR_REPO"
      value = var.backend_ecr_repository_url
    }

    environment_variable {
      name  = "FRONTEND_ECR_REPO"
      value = var.frontend_ecr_repository_url
    }

    environment_variable {
      name  = "PROJECT_NAME"
      value = var.project_name
    }

    environment_variable {
      name  = "ENVIRONMENT"
      value = var.environment
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec.yml"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "/codebuild/${var.project_name}-${var.environment}"
      stream_name = "build"
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-build"
  }
}

# CodeDeploy Application
resource "aws_codedeploy_app" "backend" {
  name             = "${var.project_name}-${var.environment}-backend"
  compute_platform = "ECS"
}

resource "aws_codedeploy_app" "frontend" {
  name             = "${var.project_name}-${var.environment}-frontend"
  compute_platform = "ECS"
}

# CodeDeploy IAM Role
resource "aws_iam_role" "codedeploy" {
  name = "${var.project_name}-${var.environment}-codedeploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codedeploy.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "codedeploy" {
  role       = aws_iam_role.codedeploy.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCodeDeployRoleForECS"
}

# CodeDeploy Deployment Groups (Blue/Green)
resource "aws_codedeploy_deployment_group" "backend" {
  app_name               = aws_codedeploy_app.backend.name
  deployment_group_name  = "${var.project_name}-${var.environment}-backend-dg"
  service_role_arn       = aws_iam_role.codedeploy.arn
  deployment_config_name = "CodeDeployDefault.ECSAllAtOnce"

  ecs_service {
    cluster_name = var.ecs_cluster_name
    service_name = var.backend_service_name
  }

  blue_green_deployment_config {
    deployment_ready_option {
      action_on_timeout = "CONTINUE_DEPLOYMENT"
    }

    terminate_blue_instances_on_deployment_success {
      action                           = "TERMINATE"
      termination_wait_time_in_minutes = 5
    }
  }

  deployment_style {
    deployment_option = "WITH_TRAFFIC_CONTROL"
    deployment_type   = "BLUE_GREEN"
  }

  load_balancer_info {
    target_group_pair_info {
      prod_traffic_route {
        listener_arns = [var.alb_listener_arn]
      }

      target_group {
        name = var.backend_target_group_name
      }

      target_group {
        name = var.backend_target_group_blue_name
      }
    }
  }

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE"]
  }
}

resource "aws_codedeploy_deployment_group" "frontend" {
  app_name               = aws_codedeploy_app.frontend.name
  deployment_group_name  = "${var.project_name}-${var.environment}-frontend-dg"
  service_role_arn       = aws_iam_role.codedeploy.arn
  deployment_config_name = "CodeDeployDefault.ECSAllAtOnce"

  ecs_service {
    cluster_name = var.ecs_cluster_name
    service_name = var.frontend_service_name
  }

  blue_green_deployment_config {
    deployment_ready_option {
      action_on_timeout = "CONTINUE_DEPLOYMENT"
    }

    terminate_blue_instances_on_deployment_success {
      action                           = "TERMINATE"
      termination_wait_time_in_minutes = 5
    }
  }

  deployment_style {
    deployment_option = "WITH_TRAFFIC_CONTROL"
    deployment_type   = "BLUE_GREEN"
  }

  load_balancer_info {
    target_group_pair_info {
      prod_traffic_route {
        listener_arns = [var.alb_listener_arn]
      }

      target_group {
        name = var.frontend_target_group_name
      }

      target_group {
        name = var.frontend_target_group_blue_name
      }
    }
  }

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE"]
  }
}

# CodePipeline IAM Role
resource "aws_iam_role" "codepipeline" {
  name = "${var.project_name}-${var.environment}-codepipeline"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codepipeline.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "codepipeline" {
  name = "${var.project_name}-${var.environment}-codepipeline-policy"
  role = aws_iam_role.codepipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.codepipeline.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "codestar-connections:UseConnection"
        ]
        Resource = var.codestar_connection_arn
      },
      {
        Effect = "Allow"
        Action = [
          "codebuild:BatchGetBuilds",
          "codebuild:StartBuild"
        ]
        Resource = aws_codebuild_project.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "codedeploy:CreateDeployment",
          "codedeploy:GetDeployment",
          "codedeploy:GetDeploymentConfig",
          "codedeploy:GetApplication",
          "codedeploy:GetApplicationRevision",
          "codedeploy:RegisterApplicationRevision"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:RegisterTaskDefinition",
          "ecs:DescribeTaskDefinition",
          "ecs:DescribeServices",
          "ecs:UpdateService"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = "*"
        Condition = {
          StringEqualsIfExists = {
            "iam:PassedToService" = [
              "ecs-tasks.amazonaws.com",
              "codedeploy.amazonaws.com"
            ]
          }
        }
      }
    ]
  })
}

# CodePipeline
resource "aws_codepipeline" "main" {
  name     = "${var.project_name}-${var.environment}-pipeline"
  role_arn = aws_iam_role.codepipeline.arn

  artifact_store {
    location = aws_s3_bucket.codepipeline.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = var.codestar_connection_arn
        FullRepositoryId = var.github_repo
        BranchName       = var.github_branch
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]
      version          = "1"

      configuration = {
        ProjectName = aws_codebuild_project.main.name
      }
    }
  }

  stage {
    name = "Deploy-Backend"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "CodeDeployToECS"
      input_artifacts = ["build_output"]
      version         = "1"

      configuration = {
        ApplicationName                = aws_codedeploy_app.backend.name
        DeploymentGroupName            = aws_codedeploy_deployment_group.backend.deployment_group_name
        TaskDefinitionTemplateArtifact = "build_output"
        TaskDefinitionTemplatePath     = "backend-taskdef.json"
        AppSpecTemplateArtifact        = "build_output"
        AppSpecTemplatePath            = "backend-appspec.yml"
      }
    }
  }

  stage {
    name = "Deploy-Frontend"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "CodeDeployToECS"
      input_artifacts = ["build_output"]
      version         = "1"

      configuration = {
        ApplicationName                = aws_codedeploy_app.frontend.name
        DeploymentGroupName            = aws_codedeploy_deployment_group.frontend.deployment_group_name
        TaskDefinitionTemplateArtifact = "build_output"
        TaskDefinitionTemplatePath     = "frontend-taskdef.json"
        AppSpecTemplateArtifact        = "build_output"
        AppSpecTemplatePath            = "frontend-appspec.yml"
      }
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-pipeline"
  }
}
```

**File: `terraform/modules/codepipeline/outputs.tf`**

```hcl
output "pipeline_name" {
  value = aws_codepipeline.main.name
}

output "codebuild_project_name" {
  value = aws_codebuild_project.main.name
}

output "artifact_bucket" {
  value = aws_s3_bucket.codepipeline.bucket
}
```

---

## Phase 2: Application Code

### 2.1 Backend Application

**File: `backend/requirements.txt`**

```
fastapi==0.109.2
uvicorn[standard]==0.27.1
pydantic==2.6.1
pydantic-settings==2.1.0
boto3==1.34.34
psycopg2-binary==2.9.9
pgvector==0.2.4
sqlalchemy==2.0.25
aws-xray-sdk==2.12.1
structlog==24.1.0
httpx==0.26.0
python-multipart==0.0.9
tenacity==8.2.3
numpy==1.26.4
```

**File: `backend/app/__init__.py`**

```python
"""RAG Backend Application"""
```

**File: `backend/app/config.py`**

```python
import json
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
import boto3


class Settings(BaseSettings):
    """Application settings loaded from environment and AWS Secrets Manager."""
    
    # App settings
    environment: str = "dev"
    aws_region: str = "us-east-1"
    log_level: str = "INFO"
    
    # Database settings (loaded from secrets)
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_username: str = ""
    db_password: str = ""
    
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
    """Load database credentials from AWS Secrets Manager."""
    secret_json = os.environ.get("DB_SECRET")
    if secret_json:
        return json.loads(secret_json)
    return {}


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    settings = Settings()
    
    # Load DB credentials from Secrets Manager
    db_creds = load_db_credentials()
    if db_creds:
        settings.db_host = db_creds.get("host", "")
        settings.db_port = db_creds.get("port", 5432)
        settings.db_name = db_creds.get("dbname", "")
        settings.db_username = db_creds.get("username", "")
        settings.db_password = db_creds.get("password", "")
    
    return settings
```

**File: `backend/app/models.py`**

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Document(BaseModel):
    """Document model for RAG corpus."""
    id: Optional[str] = None
    content: str
    metadata: dict = {}
    created_at: Optional[datetime] = None


class QueryRequest(BaseModel):
    """Query request model."""
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    """Query response model."""
    answer: str
    sources: List[dict]
    query: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class DocumentChunk(BaseModel):
    """Chunk of a document with embedding."""
    id: Optional[str] = None
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: dict = {}
```

**File: `backend/app/db/__init__.py`**

```python
"""Database module."""
```

**File: `backend/app/db/database.py`**

```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import structlog

from app.config import get_settings

logger = structlog.get_logger()
Base = declarative_base()


def get_database_url() -> str:
    """Construct database URL from settings."""
    settings = get_settings()
    return (
        f"postgresql://{settings.db_username}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )


def create_db_engine():
    """Create SQLAlchemy engine with connection pooling."""
    return create_engine(
        get_database_url(),
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )


engine = None
SessionLocal = None


def init_db():
    """Initialize database connection and create tables."""
    global engine, SessionLocal
    
    engine = create_db_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Enable pgvector extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def get_db():
    """Get database session."""
    if SessionLocal is None:
        init_db()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**File: `backend/app/db/vector_store.py`**

```python
from sqlalchemy import Column, String, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

from app.db.database import Base


class DocumentChunkModel(Base):
    """SQLAlchemy model for document chunks with vector embeddings."""
    
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String, nullable=False, index=True)
    content = Column(String, nullable=False)
    embedding = Column(Vector(1536))  # Titan embedding dimension
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index(
            'ix_document_chunks_embedding',
            embedding,
            postgresql_using='ivfflat',
            postgresql_with={'lists': 100},
            postgresql_ops={'embedding': 'vector_cosine_ops'}
        ),
    )


class VectorStore:
    """Vector store for document embeddings using pgvector."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def add_chunk(self, document_id: str, content: str, embedding: list, metadata: dict = None):
        """Add a document chunk with its embedding."""
        chunk = DocumentChunkModel(
            document_id=document_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {}
        )
        self.db.add(chunk)
        self.db.commit()
        return chunk.id
    
    def similarity_search(self, query_embedding: list, top_k: int = 5) -> list:
        """Search for similar document chunks."""
        from sqlalchemy import text
        
        # Use cosine similarity for search
        query = text("""
            SELECT id, document_id, content, metadata,
                   1 - (embedding <=> :embedding) as similarity
            FROM document_chunks
            ORDER BY embedding <=> :embedding
            LIMIT :top_k
        """)
        
        result = self.db.execute(
            query,
            {"embedding": str(query_embedding), "top_k": top_k}
        )
        
        chunks = []
        for row in result:
            chunks.append({
                "id": str(row.id),
                "document_id": row.document_id,
                "content": row.content,
                "metadata": row.metadata,
                "similarity": row.similarity
            })
        
        return chunks
    
    def delete_by_document_id(self, document_id: str):
        """Delete all chunks for a document."""
        self.db.query(DocumentChunkModel).filter(
            DocumentChunkModel.document_id == document_id
        ).delete()
        self.db.commit()
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks."""
        return self.db.query(DocumentChunkModel).count()
```

**File: `backend/app/rag/__init__.py`**

```python
"""RAG module."""
```

**File: `backend/app/rag/embeddings.py`**

```python
import json
import boto3
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()


class BedrockEmbeddings:
    """Generate embeddings using AWS Bedrock Titan."""
    
    def __init__(self):
        settings = get_settings()
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
    
    def embed_texts(self, texts: list) -> list:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = self.embed_text(text)
            embeddings.append(embedding)
        return embeddings
```

**File: `backend/app/rag/retriever.py`**

```python
import structlog
from typing import List

from app.db.vector_store import VectorStore
from app.rag.embeddings import BedrockEmbeddings

logger = structlog.get_logger()


class Retriever:
    """Retrieve relevant document chunks for a query."""
    
    def __init__(self, db_session):
        self.vector_store = VectorStore(db_session)
        self.embeddings = BedrockEmbeddings()
    
    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """Retrieve top-k relevant chunks for a query."""
        logger.info("Retrieving documents", query=query[:50], top_k=top_k)
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_text(query)
        
        # Search vector store
        results = self.vector_store.similarity_search(query_embedding, top_k=top_k)
        
        logger.info("Retrieved documents", count=len(results))
        return results
```

**File: `backend/app/rag/generator.py`**

```python
import json
import boto3
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()


class BedrockGenerator:
    """Generate responses using AWS Bedrock Llama 3."""
    
    def __init__(self):
        settings = get_settings()
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

Context:
{context}
<|eot_id|><|start_header_id|>user<|end_header_id|>

{query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        return prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, query: str, context_chunks: list) -> str:
        """Generate response using retrieved context."""
        prompt = self._build_prompt(query, context_chunks)
        
        body = json.dumps({
            "prompt": prompt,
            "max_gen_len": 512,
            "temperature": 0.7,
            "top_p": 0.9,
        })
        
        logger.info("Generating response", query=query[:50])
        
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
```

**File: `backend/app/rag/pipeline.py`**

```python
import structlog
from typing import List
import uuid

from app.rag.embeddings import BedrockEmbeddings
from app.rag.retriever import Retriever
from app.rag.generator import BedrockGenerator
from app.db.vector_store import VectorStore
from app.config import get_settings

logger = structlog.get_logger()


class RAGPipeline:
    """Full RAG pipeline: retrieve and generate."""
    
    def __init__(self, db_session):
        self.retriever = Retriever(db_session)
        self.generator = BedrockGenerator()
        self.embeddings = BedrockEmbeddings()
        self.vector_store = VectorStore(db_session)
        self.settings = get_settings()
    
    def query(self, query: str, top_k: int = None) -> dict:
        """Execute RAG query: retrieve relevant docs and generate response."""
        if top_k is None:
            top_k = self.settings.top_k_results
        
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
        
        return {
            "answer": answer,
            "sources": sources,
            "query": query
        }
    
    def ingest_document(self, content: str, metadata: dict = None) -> str:
        """Ingest a document: chunk, embed, and store."""
        document_id = str(uuid.uuid4())
        metadata = metadata or {}
        
        # Simple chunking by paragraphs/sentences
        chunks = self._chunk_text(content)
        
        logger.info("Ingesting document", document_id=document_id, chunk_count=len(chunks))
        
        for chunk in chunks:
            embedding = self.embeddings.embed_text(chunk)
            self.vector_store.add_chunk(
                document_id=document_id,
                content=chunk,
                embedding=embedding,
                metadata=metadata
            )
        
        return document_id
    
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
        
        return [c for c in chunks if c]  # Remove empty chunks
```

**File: `backend/app/seed/__init__.py`**

```python
"""Seed data module."""
```

**File: `backend/app/seed/data/sample_documents.json`**

```json
[
  {
    "title": "Introduction to Machine Learning",
    "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves. The process begins with observations or data, such as examples, direct experience, or instruction, to look for patterns in data and make better decisions in the future.\n\nThe primary aim of machine learning is to allow computers to learn automatically without human intervention or assistance and adjust actions accordingly. Machine learning algorithms are often categorized as supervised, unsupervised, or reinforcement learning.\n\nSupervised learning algorithms build a mathematical model of a set of data that contains both the inputs and the desired outputs. The data is known as training data, and consists of a set of training examples. Each training example has one or more inputs and the desired output, also known as a supervisory signal.",
    "metadata": {"category": "AI/ML", "source": "internal_docs"}
  },
  {
    "title": "Cloud Computing Fundamentals",
    "content": "Cloud computing is the delivery of computing services including servers, storage, databases, networking, software, analytics, and intelligence over the Internet to offer faster innovation, flexible resources, and economies of scale. You typically pay only for cloud services you use, helping lower operating costs, run infrastructure more efficiently, and scale as business needs change.\n\nThere are three main types of cloud computing: Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS). IaaS provides basic compute, storage, and networking resources on demand. PaaS provides a framework for developers to build upon. SaaS delivers software applications over the internet.\n\nCloud deployment models include public cloud, private cloud, and hybrid cloud. Public clouds are owned and operated by third-party cloud service providers. Private clouds are used exclusively by a single business or organization. Hybrid clouds combine public and private clouds.",
    "metadata": {"category": "Cloud", "source": "internal_docs"}
  },
  {
    "title": "Kubernetes Container Orchestration",
    "content": "Kubernetes is an open-source container orchestration platform that automates the deployment, scaling, and management of containerized applications. Originally designed by Google, it is now maintained by the Cloud Native Computing Foundation.\n\nKubernetes works with a cluster architecture consisting of a control plane and worker nodes. The control plane manages the worker nodes and the Pods in the cluster. Worker nodes host the Pods that are the components of the application workload.\n\nKey Kubernetes concepts include Pods, Services, Deployments, and ConfigMaps. A Pod is the smallest deployable unit that can be created and managed. Services define a logical set of Pods and a policy to access them. Deployments provide declarative updates for Pods and ReplicaSets. ConfigMaps allow you to decouple configuration from container images.\n\nKubernetes provides features like automatic bin packing, self-healing, horizontal scaling, service discovery and load balancing, automated rollouts and rollbacks, secret and configuration management, and storage orchestration.",
    "metadata": {"category": "DevOps", "source": "internal_docs"}
  },
  {
    "title": "Data Security Best Practices",
    "content": "Data security involves protecting digital data from unauthorized access, corruption, or theft throughout its entire lifecycle. It encompasses everything from hardware and software security to administrative controls and organizational policies.\n\nKey data security measures include encryption, which converts data into a coded form to prevent unauthorized access. Data encryption should be applied both at rest and in transit. Access control ensures that only authorized personnel can access sensitive data. This includes implementing strong authentication mechanisms and the principle of least privilege.\n\nRegular security audits and vulnerability assessments help identify and address security weaknesses. Data backup and disaster recovery planning ensure business continuity in case of data loss. Employee training on security awareness is crucial as human error is a leading cause of data breaches.\n\nCompliance with regulations such as GDPR, HIPAA, and SOC 2 is essential for organizations handling sensitive data. These regulations define requirements for data protection, privacy, and security controls that organizations must implement.",
    "metadata": {"category": "Security", "source": "internal_docs"}
  },
  {
    "title": "Retrieval-Augmented Generation (RAG)",
    "content": "Retrieval-Augmented Generation (RAG) is an AI framework that enhances large language models by retrieving relevant information from external knowledge sources before generating responses. This approach combines the strengths of retrieval-based and generation-based systems.\n\nThe RAG process typically involves three main steps: indexing, retrieval, and generation. During indexing, documents are chunked, embedded into vector representations, and stored in a vector database. At query time, the user's question is embedded and similar documents are retrieved based on vector similarity. Finally, the retrieved context is combined with the original query to generate an informed response.\n\nRAG offers several advantages over pure generative models. It provides access to up-to-date information beyond the model's training data. It reduces hallucinations by grounding responses in retrieved evidence. It allows for source attribution and verification. It can be more cost-effective than fine-tuning large models for specific domains.\n\nCommon vector databases used in RAG systems include Pinecone, Weaviate, Milvus, and pgvector. Popular embedding models include OpenAI's text-embedding-ada-002, Cohere's embed models, and open-source options like sentence-transformers.",
    "metadata": {"category": "AI/ML", "source": "internal_docs"}
  }
]
```

**File: `backend/app/seed/corpus.py`**

```python
import json
import os
import structlog

from app.rag.pipeline import RAGPipeline

logger = structlog.get_logger()


def load_sample_documents() -> list:
    """Load sample documents from JSON file."""
    data_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "sample_documents.json"
    )
    
    with open(data_path, "r") as f:
        return json.load(f)


def seed_corpus(db_session) -> int:
    """Seed the vector store with sample documents."""
    pipeline = RAGPipeline(db_session)
    documents = load_sample_documents()
    
    logger.info("Seeding corpus", document_count=len(documents))
    
    ingested_count = 0
    for doc in documents:
        try:
            document_id = pipeline.ingest_document(
                content=doc["content"],
                metadata={
                    "title": doc.get("title", ""),
                    **doc.get("metadata", {})
                }
            )
            logger.info("Ingested document", title=doc.get("title"), document_id=document_id)
            ingested_count += 1
        except Exception as e:
            logger.error("Failed to ingest document", title=doc.get("title"), error=str(e))
    
    return ingested_count
```

**File: `backend/app/main.py`**

```python
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import structlog

# X-Ray instrumentation
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

from app.config import get_settings
from app.models import QueryRequest, QueryResponse, HealthResponse
from app.db.database import get_db, init_db
from app.db.vector_store import VectorStore
from app.rag.pipeline import RAGPipeline
from app.seed.corpus import seed_corpus

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configure X-Ray
xray_recorder.configure(
    service="rag-backend",
    daemon_address=os.environ.get("AWS_XRAY_DAEMON_ADDRESS", "localhost:2000"),
    context_missing="LOG_ERROR"
)
patch_all()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting application")
    
    # Initialize database
    init_db()
    
    # Seed corpus if empty
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        vector_store = VectorStore(db)
        if vector_store.get_chunk_count() == 0:
            logger.info("Seeding initial corpus")
            seed_corpus(db)
    finally:
        db.close()
    
    yield
    
    logger.info("Shutting down application")


app = FastAPI(
    title="RAG Backend API",
    description="Retrieval-Augmented Generation backend service",
    version="1.0.0",
    lifespan=lifespan
)

# Add X-Ray middleware
app.add_middleware(XRayMiddleware, recorder=xray_recorder)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, db: Session = Depends(get_db)):
    """Query the RAG system."""
    logger.info("Received query", query=request.query[:50])
    
    try:
        pipeline = RAGPipeline(db)
        result = pipeline.query(request.query, top_k=request.top_k)
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            query=result["query"]
        )
    except Exception as e:
        logger.error("Query failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    vector_store = VectorStore(db)
    
    return {
        "chunk_count": vector_store.get_chunk_count(),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**File: `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2 Frontend Application (Streamlit)

**File: `frontend/requirements.txt`**

```
streamlit==1.31.0
httpx==0.26.0
```

**File: `frontend/app.py`**

```python
import os
import streamlit as st
import httpx

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RAG Chat",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 RAG Chat Interface")
st.markdown("Ask questions about the knowledge base.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"**Source {i}** (similarity: {source['similarity']})")
                    st.markdown(f"> {source['content']}")

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response from backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = httpx.post(
                    f"{BACKEND_URL}/api/query",
                    json={"query": prompt, "top_k": 5},
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                st.markdown(data["answer"])
                
                # Show sources
                if data["sources"]:
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(data["sources"], 1):
                            st.markdown(f"**Source {i}** (similarity: {source['similarity']})")
                            st.markdown(f"> {source['content']}")
                
                # Add to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data["answer"],
                    "sources": data["sources"]
                })
                
            except httpx.HTTPStatusError as e:
                st.error(f"Backend error: {e.response.status_code}")
            except httpx.RequestError as e:
                st.error(f"Connection error: {str(e)}")

# Sidebar with stats
with st.sidebar:
    st.header("System Info")
    
    try:
        stats = httpx.get(f"{BACKEND_URL}/api/stats", timeout=5.0).json()
        st.metric("Documents Indexed", stats.get("chunk_count", 0))
    except:
        st.warning("Could not fetch stats")
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
```

**File: `frontend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
```

---

## Phase 3: CI/CD Configuration

### 3.1 Build Specification

**File: `buildspec.yml`**

```yaml
version: 0.2

env:
  variables:
    DOCKER_BUILDKIT: "1"

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}

  build:
    commands:
      - echo Build started on `date`
      
      # Build backend image
      - echo Building backend Docker image...
      - docker build -t $BACKEND_ECR_REPO:latest -t $BACKEND_ECR_REPO:$IMAGE_TAG ./backend
      
      # Build frontend image
      - echo Building frontend Docker image...
      - docker build -t $FRONTEND_ECR_REPO:latest -t $FRONTEND_ECR_REPO:$IMAGE_TAG ./frontend

  post_build:
    commands:
      - echo Build completed on `date`
      
      # Push backend images
      - echo Pushing backend Docker image...
      - docker push $BACKEND_ECR_REPO:latest
      - docker push $BACKEND_ECR_REPO:$IMAGE_TAG
      
      # Push frontend images
      - echo Pushing frontend Docker image...
      - docker push $FRONTEND_ECR_REPO:latest
      - docker push $FRONTEND_ECR_REPO:$IMAGE_TAG
      
      # Wait for ECR scan results
      - echo Waiting for ECR scan results...
      - |
        for repo in "$PROJECT_NAME-$ENVIRONMENT-backend" "$PROJECT_NAME-$ENVIRONMENT-frontend"; do
          echo "Checking scan for $repo:$IMAGE_TAG"
          aws ecr wait image-scan-complete --repository-name $repo --image-id imageTag=$IMAGE_TAG --region $AWS_REGION || true
          SCAN_FINDINGS=$(aws ecr describe-image-scan-findings --repository-name $repo --image-id imageTag=$IMAGE_TAG --region $AWS_REGION --query 'imageScanFindings.findingSeverityCounts' --output json 2>/dev/null || echo '{}')
          echo "Scan findings for $repo: $SCAN_FINDINGS"
          CRITICAL=$(echo $SCAN_FINDINGS | jq -r '.CRITICAL // 0')
          if [ "$CRITICAL" != "0" ] && [ "$CRITICAL" != "null" ]; then
            echo "WARNING: Critical vulnerabilities found in $repo"
          fi
        done
      
      # Generate task definition files for CodeDeploy
      - echo Generating deployment artifacts...
      
      # Backend task definition
      - |
        cat > backend-taskdef.json << EOF
        {
          "family": "$PROJECT_NAME-$ENVIRONMENT-backend",
          "networkMode": "awsvpc",
          "requiresCompatibilities": ["FARGATE"],
          "cpu": "512",
          "memory": "1024",
          "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/$PROJECT_NAME-$ENVIRONMENT-ecs-task-execution",
          "taskRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/$PROJECT_NAME-$ENVIRONMENT-ecs-task",
          "containerDefinitions": [
            {
              "name": "backend",
              "image": "<IMAGE1_NAME>",
              "portMappings": [
                {
                  "containerPort": 8000,
                  "hostPort": 8000,
                  "protocol": "tcp"
                }
              ],
              "essential": true,
              "environment": [
                {"name": "AWS_REGION", "value": "$AWS_REGION"},
                {"name": "ENVIRONMENT", "value": "$ENVIRONMENT"},
                {"name": "AWS_XRAY_DAEMON_ADDRESS", "value": "localhost:2000"}
              ],
              "secrets": [
                {
                  "name": "DB_SECRET",
                  "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:$PROJECT_NAME-$ENVIRONMENT-db-credentials"
                }
              ],
              "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                  "awslogs-group": "/ecs/$PROJECT_NAME-$ENVIRONMENT",
                  "awslogs-region": "$AWS_REGION",
                  "awslogs-stream-prefix": "backend"
                }
              },
              "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
              }
            },
            {
              "name": "xray-daemon",
              "image": "amazon/aws-xray-daemon:latest",
              "portMappings": [
                {
                  "containerPort": 2000,
                  "hostPort": 2000,
                  "protocol": "udp"
                }
              ],
              "essential": false,
              "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                  "awslogs-group": "/ecs/$PROJECT_NAME-$ENVIRONMENT",
                  "awslogs-region": "$AWS_REGION",
                  "awslogs-stream-prefix": "xray"
                }
              },
              "cpu": 32,
              "memory": 256
            }
          ]
        }
        EOF
      
      # Frontend task definition
      - |
        cat > frontend-taskdef.json << EOF
        {
          "family": "$PROJECT_NAME-$ENVIRONMENT-frontend",
          "networkMode": "awsvpc",
          "requiresCompatibilities": ["FARGATE"],
          "cpu": "256",
          "memory": "512",
          "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/$PROJECT_NAME-$ENVIRONMENT-ecs-task-execution",
          "taskRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/$PROJECT_NAME-$ENVIRONMENT-ecs-task",
          "containerDefinitions": [
            {
              "name": "frontend",
              "image": "<IMAGE2_NAME>",
              "portMappings": [
                {
                  "containerPort": 8501,
                  "hostPort": 8501,
                  "protocol": "tcp"
                }
              ],
              "essential": true,
              "environment": [
                {"name": "BACKEND_URL", "value": "http://backend.$PROJECT_NAME.local:8000"},
                {"name": "ENVIRONMENT", "value": "$ENVIRONMENT"}
              ],
              "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                  "awslogs-group": "/ecs/$PROJECT_NAME-$ENVIRONMENT",
                  "awslogs-region": "$AWS_REGION",
                  "awslogs-stream-prefix": "frontend"
                }
              },
              "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
              }
            }
          ]
        }
        EOF
      
      # Backend AppSpec
      - |
        cat > backend-appspec.yml << EOF
        version: 0.0
        Resources:
          - TargetService:
              Type: AWS::ECS::Service
              Properties:
                TaskDefinition: <TASK_DEFINITION>
                LoadBalancerInfo:
                  ContainerName: "backend"
                  ContainerPort: 8000
        EOF
      
      # Frontend AppSpec
      - |
        cat > frontend-appspec.yml << EOF
        version: 0.0
        Resources:
          - TargetService:
              Type: AWS::ECS::Service
              Properties:
                TaskDefinition: <TASK_DEFINITION>
                LoadBalancerInfo:
                  ContainerName: "frontend"
                  ContainerPort: 8501
        EOF
      
      # Create imageDetail.json for CodeDeploy
      - printf '{"ImageURI":"%s"}' $BACKEND_ECR_REPO:$IMAGE_TAG > backend-imageDetail.json
      - printf '{"ImageURI":"%s"}' $FRONTEND_ECR_REPO:$IMAGE_TAG > frontend-imageDetail.json

artifacts:
  files:
    - backend-taskdef.json
    - frontend-taskdef.json
    - backend-appspec.yml
    - frontend-appspec.yml
    - backend-imageDetail.json
    - frontend-imageDetail.json
```

---

## Phase 4: Deployment

### 4.1 Pre-Deployment Setup

**Create CodeStar Connection for GitHub:**

```bash
# Create connection (must be done via Console or CLI)
aws codestar-connections create-connection \
    --provider-type GitHub \
    --connection-name ecs-rag-github \
    --region us-east-1

# Note the ConnectionArn from output
# Then go to AWS Console → Developer Tools → Settings → Connections
# Click on the connection and complete the OAuth handshake with GitHub
```

### 4.2 Deploy Infrastructure

**File: `scripts/deploy.sh`**

```bash
#!/bin/bash
set -e

echo "=== ECS RAG Project Deployment ==="

# Configuration
PROJECT_NAME="ecs-rag"
ENVIRONMENT="dev"
REGION="us-east-1"
GITHUB_REPO="your-username/ecs-rag-project"  # UPDATE THIS
GITHUB_BRANCH="main"

# Get CodeStar connection ARN (must be created beforehand)
CODESTAR_ARN=$(aws codestar-connections list-connections \
    --provider-type GitHub \
    --query "Connections[?ConnectionName=='ecs-rag-github'].ConnectionArn" \
    --output text \
    --region $REGION)

if [ -z "$CODESTAR_ARN" ]; then
    echo "Error: CodeStar connection not found. Create it first."
    exit 1
fi

echo "Using CodeStar connection: $CODESTAR_ARN"

# Navigate to terraform directory
cd terraform

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Plan deployment
echo "Planning infrastructure..."
terraform plan \
    -var="project_name=$PROJECT_NAME" \
    -var="environment=$ENVIRONMENT" \
    -var="aws_region=$REGION" \
    -var="github_repo=$GITHUB_REPO" \
    -var="github_branch=$GITHUB_BRANCH" \
    -var="codestar_connection_arn=$CODESTAR_ARN" \
    -out=tfplan

# Apply deployment
read -p "Apply infrastructure? (yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    echo "Applying infrastructure..."
    terraform apply tfplan
    
    echo ""
    echo "=== Deployment Complete ==="
    echo "ALB DNS: $(terraform output -raw alb_dns_name)"
    echo "Backend ECR: $(terraform output -raw backend_ecr_repository_url)"
    echo "Frontend ECR: $(terraform output -raw frontend_ecr_repository_url)"
else
    echo "Deployment cancelled."
fi
```

### 4.3 Initial Image Push

Before the pipeline can work, push initial images:

```bash
#!/bin/bash
# scripts/initial-push.sh

REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
PROJECT_NAME="ecs-rag"
ENVIRONMENT="dev"

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build and push backend
cd backend
docker build -t $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-backend:latest .
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-backend:latest

# Build and push frontend
cd ../frontend
docker build -t $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-frontend:latest .
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-frontend:latest

echo "Initial images pushed successfully"
```

---

## Phase 5: Testing & Validation

### 5.1 Verify Deployment

```bash
# Get ALB DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --names ecs-rag-dev-alb \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

# Test health endpoint
curl http://$ALB_DNS/health

# Test RAG query
curl -X POST http://$ALB_DNS/api/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What is machine learning?", "top_k": 3}'

# Access Streamlit UI
echo "Open in browser: http://$ALB_DNS"
```

### 5.2 Verify Monitoring

```bash
# Check CloudWatch logs
aws logs tail /ecs/ecs-rag-dev --follow

# View X-Ray traces
# Console → X-Ray → Traces

# View CloudWatch dashboard
# Console → CloudWatch → Dashboards → ecs-rag-dev-dashboard

# Check Container Insights
# Console → CloudWatch → Container Insights → ECS Services
```

### 5.3 Verify Security

```bash
# Check ECR scan results
aws ecr describe-image-scan-findings \
    --repository-name ecs-rag-dev-backend \
    --image-id imageTag=latest

# Check GuardDuty findings
aws guardduty list-findings \
    --detector-id $(aws guardduty list-detectors --query 'DetectorIds[0]' --output text)

# Check GuardDuty ECS Runtime Monitoring
aws guardduty get-detector \
    --detector-id $(aws guardduty list-detectors --query 'DetectorIds[0]' --output text) \
    --query 'Features[?Name==`ECS_RUNTIME_MONITORING`]'
```

### 5.4 Test Blue/Green Deployment

```bash
# Make a code change, commit, and push
git add .
git commit -m "Test blue/green deployment"
git push origin main

# Monitor deployment in CodePipeline
aws codepipeline get-pipeline-state --name ecs-rag-dev-pipeline

# Watch ECS service updates
aws ecs describe-services \
    --cluster ecs-rag-dev-cluster \
    --services ecs-rag-dev-backend-service \
    --query 'services[0].deployments'
```

---

## Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy \
    -var="project_name=ecs-rag" \
    -var="environment=dev" \
    -var="aws_region=us-east-1" \
    -var="github_repo=your-username/ecs-rag-project" \
    -var="github_branch=main" \
    -var="codestar_connection_arn=YOUR_CODESTAR_ARN"

# Also delete:
# - S3 bucket for Terraform state
# - DynamoDB table for state locking
# - CodeStar connection
# - CloudWatch log groups (if not deleted by Terraform)
```

---

## Troubleshooting

### Common Issues

1. **ECS tasks failing to start**: Check CloudWatch logs for the task. Common issues:
   - ECR image pull failures → Check VPC endpoints
   - Secrets Manager access → Check IAM roles
   - Database connection → Check security groups

2. **Bedrock access denied**: Ensure model access is granted in Bedrock console and IAM policy is correct.

3. **ALB health checks failing**: 
   - Check security groups allow ALB → ECS traffic
   - Verify health check paths match application endpoints

4. **CodeDeploy deployment stuck**:
   - Check CodeDeploy logs in CloudWatch
   - Verify target groups are configured correctly
   - Check ECS service events for errors

5. **VPC endpoint issues**:
   - Ensure private DNS is enabled
   - Check security group allows HTTPS from VPC CIDR

### Useful Commands

```bash
# ECS task logs
aws logs get-log-events \
    --log-group-name /ecs/ecs-rag-dev \
    --log-stream-name backend/backend/TASK_ID

# Force new deployment
aws ecs update-service \
    --cluster ecs-rag-dev-cluster \
    --service ecs-rag-dev-backend-service \
    --force-new-deployment

# Describe ECS service events
aws ecs describe-services \
    --cluster ecs-rag-dev-cluster \
    --services ecs-rag-dev-backend-service \
    --query 'services[0].events[:10]'
```

---

## Cost Estimation (Monthly)

| Resource | Estimated Cost |
|----------|----------------|
| ECS Fargate (backend: 2 tasks) | ~$30 |
| ECS Fargate (frontend: 1 task) | ~$10 |
| RDS PostgreSQL (db.t3.micro) | ~$15 |
| ALB | ~$20 |
| VPC Endpoints (8 interface endpoints) | ~$60 |
| CloudWatch Logs | ~$5 |
| Bedrock API calls | Variable (pay-per-use) |
| **Total (excluding Bedrock)** | **~$140/month** |

**Cost optimization for learning:**
- Use Fargate Spot for non-production
- Reduce VPC endpoints (accept NAT Gateway instead)
- Scale down RDS to smaller instance
- Stop resources when not in use

---

## Phase 2 Readiness Review - Deferred Decisions

### Decisions Made

Based on the Phase 2 readiness review, the following architectural decisions have been made:

#### 1. Database Seeding Strategy
**Decision**: Add PostgreSQL advisory lock to prevent race conditions
- Auto-seed on first startup with protection using advisory lock (lock_id=1)
- Only one ECS task can seed at a time, preventing duplicate data
- Leverages existing PostgreSQL functionality without creating new resources
- Implementation in `backend/app/db/database.py` and `backend/app/seed/corpus.py`

#### 2. BACKEND_URL Environment Variable
**Decision**: Hardcode the backend URL in buildspec.yml
- Fixed value: `http://backend.ecs-rag.local:8000`
- Replaces variable interpolation `$PROJECT_NAME` that wouldn't work at runtime
- Uses existing service discovery namespace `ecs-rag.local`
- No new resources required

#### 3. X-Ray Sampling Rate
**Decision**: Set to 100% for development visibility
- Changed from 10% to 100% sampling rate
- Better debugging visibility for learning project
- Updated in `terraform/modules/monitoring/main.tf`
- Appropriate since this is not a production environment

#### 4. Bedrock Failure Behavior
**Decision**: Keep fail-fast approach
- Return 500 error to user after 3 retries with exponential backoff
- No graceful degradation or circuit breaker pattern
- Simpler implementation appropriate for learning project
- Existing retry logic in `backend/app/rag/embeddings.py` and `backend/app/rag/generator.py`

### Implementation Notes

- All changes leverage existing Terraform resources
- No new AWS resources need to be created
- Advisory lock uses PostgreSQL's built-in `pg_advisory_lock()` function
- Service discovery already configured in ECS module
- X-Ray sampling is a simple configuration change

### Next Steps for Phase 2

With these decisions made, Phase 2 application development can proceed with:
1. RAG pipeline implementation
2. FastAPI backend development
3. Streamlit frontend development
4. Testing and validation
5. CI/CD pipeline configuration