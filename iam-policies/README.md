# IAM Policies for SageMaker Execution Role

This directory contains least-privilege IAM policies required for your SageMaker execution role to run the Terraform configuration.

## Policy Files

1. **01-networking-policy.json** - VPC, subnets, route tables, internet gateway, security groups, VPC endpoints
2. **02-compute-ecs-ecr-policy.json** - ECS clusters, task definitions, services, ECR repositories
3. **03-database-policy.json** - RDS instances, Secrets Manager
4. **04-load-balancer-policy.json** - Application Load Balancer, target groups, listeners
5. **05-security-guardduty-policy.json** - GuardDuty detector and features
6. **06-monitoring-policy.json** - CloudWatch Logs, metrics, alarms, dashboards, X-Ray
7. **07-cicd-pipeline-policy.json** - CodePipeline, CodeBuild, CodeDeploy, S3, CodeStar Connections
8. **08-iam-management-policy.json** - IAM roles and policies (for resources created by Terraform)
9. **09-read-only-policy.json** - Read/describe permissions for AWS account information

## How to Apply These Policies

### Option 1: Apply All Policies via AWS Console

1. Navigate to IAM → Policies → Create Policy
2. For each JSON file:
   - Click "JSON" tab
   - Copy the contents of the policy file
   - Paste into the editor
   - Click "Next: Tags" → "Next: Review"
   - Name the policy (e.g., "SageMaker-ECS-RAG-Networking")
   - Create the policy
3. Navigate to your SageMaker execution role
4. Click "Attach policies"
5. Search for and attach all 9 policies you created

### Option 2: Apply All Policies via AWS CLI

```bash
# Set your role name
ROLE_NAME="your-sagemaker-execution-role-name"

# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create and attach each policy
for policy_file in iam-policies/*.json; do
    policy_name="SageMaker-ECS-RAG-$(basename "$policy_file" .json)"

    # Create the policy
    policy_arn=$(aws iam create-policy \
        --policy-name "$policy_name" \
        --policy-document "file://$policy_file" \
        --query 'Policy.Arn' \
        --output text 2>/dev/null)

    # If policy already exists, get its ARN
    if [ -z "$policy_arn" ]; then
        policy_arn="arn:aws:iam::${ACCOUNT_ID}:policy/${policy_name}"
    fi

    # Attach the policy to the role
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "$policy_arn"

    echo "Attached: $policy_name"
done
```

### Option 3: Create a Single Combined Policy (Less Granular)

If you prefer a single policy, you can combine all statements into one policy document. However, note that AWS has a managed policy size limit of 6,144 characters, so you may need to split into 2-3 policies.

## Verification

After applying the policies, verify they're attached:

```bash
aws iam list-attached-role-policies --role-name your-sagemaker-execution-role-name
```

## Security Notes

- These policies follow the principle of least privilege
- Resource wildcards (*) are used where Terraform needs to create resources with dynamic names
- The IAM PassRole permission is restricted to specific AWS services
- Read-only permissions are separated for easy auditing
- Consider further restricting policies in production by:
  - Adding resource ARN conditions where possible
  - Limiting actions to specific resource tags
  - Using IAM condition keys for additional constraints

## Terraform State Backend Access

Don't forget to also ensure your role has access to the S3 bucket and DynamoDB table for Terraform state (see PREREQUISITES.md).
