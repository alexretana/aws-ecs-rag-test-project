#!/bin/bash

# Script to create and attach IAM policies to a SageMaker execution role
# Usage: ./apply-policies.sh <role-name>

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <role-name>"
    echo "Example: $0 my-sagemaker-execution-role"
    exit 1
fi

ROLE_NAME="$1"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get AWS account ID
echo "Getting AWS account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Verify role exists
echo "Verifying role exists: $ROLE_NAME"
if ! aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
    echo "Error: Role '$ROLE_NAME' does not exist"
    exit 1
fi

echo "Processing policy files..."

# Create and attach each policy
for policy_file in "$SCRIPT_DIR"/*.json; do
    # Skip non-json files
    [ -f "$policy_file" ] || continue

    policy_basename=$(basename "$policy_file" .json)
    policy_name="SageMaker-ECS-RAG-${policy_basename}"

    echo ""
    echo "Processing: $policy_basename"

    # Try to create the policy
    policy_arn=$(aws iam create-policy \
        --policy-name "$policy_name" \
        --policy-document "file://$policy_file" \
        --description "IAM policy for ECS RAG Terraform deployment - $policy_basename" \
        --query 'Policy.Arn' \
        --output text 2>/dev/null || true)

    # If policy already exists, get its ARN
    if [ -z "$policy_arn" ]; then
        echo "  Policy already exists, getting ARN..."
        policy_arn="arn:aws:iam::${ACCOUNT_ID}:policy/${policy_name}"
    else
        echo "  Created policy: $policy_name"
    fi

    # Attach the policy to the role
    if aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "$policy_arn" 2>/dev/null; then
        echo "  ✓ Attached: $policy_name"
    else
        echo "  ℹ Already attached: $policy_name"
    fi
done

echo ""
echo "================================================"
echo "Policy application complete!"
echo "================================================"
echo ""
echo "Attached policies:"
aws iam list-attached-role-policies --role-name "$ROLE_NAME" --query 'AttachedPolicies[?contains(PolicyName, `ECS-RAG`)].PolicyName' --output table

echo ""
echo "Next steps:"
echo "1. Review PREREQUISITES.md for remaining setup tasks"
echo "2. Create Terraform backend (S3 bucket + DynamoDB table)"
echo "3. Set up CodeStar connection to GitHub"
echo "4. Create terraform.tfvars with your configuration"
echo "5. Run: cd terraform && terraform init && terraform plan"
