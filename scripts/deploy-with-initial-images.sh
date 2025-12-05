#!/bin/bash

# Deployment script for ECS RAG project with initial ECR images
# This script automates the process of pushing placeholder images to ECR
# before deploying the full infrastructure

set -e

echo "=== ECS RAG Project Deployment with Initial ECR Images ==="
echo ""

# Check if Docker is installed and running
echo "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker before running this script."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "ERROR: Docker is not running. Please start Docker before running this script."
    exit 1
fi

echo "✓ Docker is installed and running"
echo ""

# Check if AWS CLI is installed
echo "Checking AWS CLI installation..."
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed. Please install AWS CLI before running this script."
    exit 1
fi

echo "✓ AWS CLI is installed"
echo ""

# Check if Terraform is installed
echo "Checking Terraform installation..."
if ! command -v terraform &> /dev/null; then
    echo "ERROR: Terraform is not installed. Please install Terraform before running this script."
    exit 1
fi

echo "✓ Terraform is installed"
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials are not configured. Please run 'aws configure' or set up environment variables."
    exit 1
fi

echo "✓ AWS credentials are configured"
echo ""

# Change to terraform directory
cd terraform

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

echo ""
echo "=== Starting Deployment ==="
echo ""
echo "This deployment will:"
echo "1. Create all infrastructure including ECR repositories"
echo "2. Automatically push placeholder images to ECR"
echo "3. Deploy ECS services with the placeholder images"
echo "4. Set up CodePipeline for future deployments"
echo ""

read -p "Do you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Apply Terraform
echo ""
echo "Running Terraform apply..."
echo "This will take some time as it creates all resources and pushes images..."
echo ""

terraform apply

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Your ECS RAG application has been deployed with placeholder images."
echo ""
echo "Next steps:"
echo "1. Build your actual application images"
echo "2. Push them to the ECR repositories"
echo "3. Trigger a new deployment via CodePipeline"
echo ""
echo "ECR Repository URLs:"
echo "Backend: $(terraform output -raw | grep backend_ecr_repository_url | cut -d' ' -f3)"
echo "Frontend: $(terraform output -raw | grep frontend_ecr_repository_url | cut -d' ' -f3)"
echo ""
echo "Load Balancer URL:"
echo "Application: $(terraform output -raw | grep -E "(alb_dns_name|load_balancer_dns)" | cut -d' ' -f3 || echo "Check Terraform outputs for ALB DNS name")"