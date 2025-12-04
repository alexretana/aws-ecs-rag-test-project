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