#!/bin/bash

# Destroy script for ECS RAG project
# This script safely destroys all Terraform-managed infrastructure

set -e

echo "=== ECS RAG Project Infrastructure Destruction ==="
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

# Check if backend.config exists
if [ ! -f "backend.config" ]; then
    echo "ERROR: backend.config file not found in terraform directory"
    echo ""
    echo "Cannot proceed without backend configuration."
    exit 1
fi

# Initialize Terraform with backend config
echo "Initializing Terraform with backend configuration..."
terraform init -backend-config=backend.config -reconfigure

echo ""
echo "=== WARNING: Infrastructure Destruction ==="
echo ""
echo "This will DESTROY all infrastructure including:"
echo "  - ECS clusters and services"
echo "  - RDS database instances"
echo "  - Application Load Balancer"
echo "  - VPC and networking resources"
echo "  - ECR repositories (images will be deleted)"
echo "  - CodePipeline and associated resources"
echo "  - CloudWatch logs and monitoring"
echo "  - Security groups and IAM roles"
echo ""
echo "This action is IRREVERSIBLE and will result in DATA LOSS!"
echo ""

read -p "Are you absolutely sure you want to destroy ALL infrastructure? (yes/NO): " -r
echo
if [[ ! $REPLY == "yes" ]]; then
    echo "Destruction cancelled."
    exit 0
fi

# Show Terraform destroy plan for confirmation
echo ""
echo "Generating Terraform destroy plan..."
echo "This will show all resources that will be destroyed..."
echo ""

terraform plan -destroy -out=tfdestroy

echo ""
echo "=== Terraform Destroy Plan Complete ==="
echo ""
echo "Please review the plan above carefully."
echo "All listed resources will be PERMANENTLY DESTROYED."
echo ""

read -p "Type 'destroy' to proceed with destruction: " -r
echo
if [[ ! $REPLY == "destroy" ]]; then
    echo "Destruction cancelled."
    echo "Cleaning up plan file..."
    rm -f tfdestroy
    exit 0
fi

# Apply Terraform destroy using saved plan
echo ""
echo "Running Terraform destroy with saved plan..."
echo "This may take several minutes..."
echo ""

terraform apply tfdestroy

# Clean up plan file
echo ""
echo "Cleaning up plan file..."
rm -f tfdestroy

echo ""
echo "=== Infrastructure Destruction Complete ==="
echo ""
echo "All Terraform-managed resources have been destroyed."
echo ""
echo "Note: The following resources are NOT destroyed by this script:"
echo "  - S3 bucket for Terraform state"
echo "  - Any manually created resources outside of Terraform"
echo ""
echo "If you want to completely clean up, you may manually delete:"
echo "  1. The Terraform state S3 bucket"
echo "  2. Any remaining CloudWatch log groups"
echo "  3. Any ECR images that were protected from deletion"