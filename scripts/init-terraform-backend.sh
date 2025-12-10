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

echo ""
echo "Terraform backend created successfully:"
echo "  S3 Bucket: ${BUCKET_NAME}"
echo "  Region: ${REGION}"
echo ""
echo "Note: State locking will use S3-based lockfiles (.tflock)"
echo "      No DynamoDB table is required with use_lockfile=true"