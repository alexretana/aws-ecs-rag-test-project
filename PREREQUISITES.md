# Prerequisites for Running Terraform

Before running `terraform plan` or `terraform apply`, you must complete the following prerequisite tasks.

## 1. Create Backend Configuration File

The Terraform backend uses partial configuration to avoid hardcoding sensitive information.

### Steps:

```bash
cd terraform

# Copy the example file
cp backend.config.example backend.config

# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Edit backend.config and replace YOUR_ACCOUNT_ID with your actual account ID
# Or use sed to do it automatically:
sed -i "s/YOUR_ACCOUNT_ID/$ACCOUNT_ID/g" backend.config
```

The `backend.config` file is already in `.gitignore` and will not be committed to version control.

## 2. Run Your Backend Initialization Script

You mentioned you have a script to initialize the DynamoDB table and S3 bucket for Terraform state management. Run that script now to create:

- S3 bucket: `ecs-rag-project-tfstate-<YOUR-ACCOUNT-ID>`
- DynamoDB table: `ecs-rag-project-tflock`

Make sure the bucket name and table name match what's in your `backend.config` file.

### Alternative: Manual Creation via AWS Console (if you don't have a script)

1. **Create S3 Bucket**:
   - Navigate to S3 → Create bucket
   - Name: `ecs-rag-project-tfstate-<YOUR-ACCOUNT-ID>`
   - Region: `us-east-1`
   - Enable versioning
   - Enable default encryption (SSE-S3 or SSE-KMS)
   - Block all public access

2. **Create DynamoDB Table**:
   - Navigate to DynamoDB → Create table
   - Table name: `ecs-rag-project-tflock`
   - Partition key: `LockID` (String)
   - Use default settings
   - Click Create

### Alternative: Automated Creation via AWS CLI

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create S3 bucket for Terraform state
aws s3api create-bucket \
    --bucket "ecs-rag-project-tfstate-${ACCOUNT_ID}" \
    --region us-east-1

# Enable versioning on the bucket
aws s3api put-bucket-versioning \
    --bucket "ecs-rag-project-tfstate-${ACCOUNT_ID}" \
    --versioning-configuration Status=Enabled

# Enable default encryption
aws s3api put-bucket-encryption \
    --bucket "ecs-rag-project-tfstate-${ACCOUNT_ID}" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Block public access
aws s3api put-public-access-block \
    --bucket "ecs-rag-project-tfstate-${ACCOUNT_ID}" \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Create DynamoDB table for state locking
aws dynamodb create-table \
    --table-name ecs-rag-project-tflock \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

### Grant SageMaker Role Access to Backend

Your SageMaker execution role needs access to the S3 bucket and DynamoDB table. Create and attach this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TerraformStateS3",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::ecs-rag-project-tfstate-<YOUR-ACCOUNT-ID>",
        "arn:aws:s3:::ecs-rag-project-tfstate-<YOUR-ACCOUNT-ID>/*"
      ]
    },
    {
      "Sid": "TerraformStateDynamoDB",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:DescribeTable"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:<YOUR-ACCOUNT-ID>:table/ecs-rag-project-tflock"
    }
  ]
}
```

## 3. Create CodeStar Connection for GitHub

The CodePipeline module requires a CodeStar connection to GitHub.

### Steps:

1. Navigate to AWS Console → Developer Tools → Connections
2. Click "Create connection"
3. Select "GitHub" as the provider
4. Enter a connection name (e.g., "ecs-rag-github")
5. Click "Connect to GitHub"
6. Authorize AWS to access your GitHub account
7. Copy the connection ARN (format: `arn:aws:codestar-connections:us-east-1:123456789012:connection/abc123...`)

## 4. Prepare Terraform Variables

Create your `terraform.tfvars` file from the example:

```bash
cd terraform

# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars and fill in your values
# Required changes:
# - github_repo: your-github-username/your-repo-name
# - codestar_connection_arn: (from step 3)
# Optional changes based on your preferences:
# - project_name, environment, aws_region, etc.
```

The `terraform.tfvars` file is already in `.gitignore` and will not be committed to version control.

**Important**: Do not commit `terraform.tfvars` to GitHub as it may contain sensitive information.

## 5. Apply IAM Policies to SageMaker Role

Follow the instructions in `iam-policies/README.md` to attach all required IAM policies to your SageMaker execution role.

## 6. Handle Initial ECR Images

The ECS task definitions reference ECR images with `:latest` tag. You have two options:

### Option A: Modify Task Definitions to Use Placeholder Images

Temporarily modify the task definitions to use public images:

```hcl
# In terraform/modules/ecs/main.tf
# Change image lines to:
image = "public.ecr.aws/docker/library/hello-world:latest"
```

After the first deployment, update back to use your ECR repositories.

### Option B: Push Initial Images Before Running Terraform

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Create repositories manually first
aws ecr create-repository --repository-name ecs-rag-dev-backend --region us-east-1
aws ecr create-repository --repository-name ecs-rag-dev-frontend --region us-east-1

# Build and push placeholder images
docker pull public.ecr.aws/docker/library/hello-world:latest
docker tag public.ecr.aws/docker/library/hello-world:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ecs-rag-dev-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ecs-rag-dev-backend:latest
docker tag public.ecr.aws/docker/library/hello-world:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ecs-rag-dev-frontend:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ecs-rag-dev-frontend:latest
```

### Option C: Recommended - Let Terraform Create ECR, Then Push Images

1. Comment out the ECS service resources initially
2. Run terraform apply to create ECR repositories
3. Push your images
4. Uncomment ECS services and run terraform apply again

## 7. Verify Bedrock Model Access

Your AWS account needs access to the Bedrock models specified in the Terraform configuration:
- `amazon.titan-embed-text-v1`
- `meta.llama3-8b-instruct-v1:0`

### Steps:

1. Navigate to AWS Bedrock console
2. Go to "Model access" in the left sidebar
3. Request access to:
   - Amazon Titan Embeddings models
   - Meta Llama 3 models
4. Wait for access to be granted (usually instant for some models, may take time for others)

## Checklist

Before running `terraform init`:

- [ ] Created `backend.config` from `backend.config.example` with your account ID
- [ ] Ran your backend initialization script (or manually created S3 bucket and DynamoDB table)
- [ ] Granted SageMaker role access to S3 bucket and DynamoDB table
- [ ] Applied all 9 IAM policies to SageMaker execution role
- [ ] Created CodeStar connection to GitHub
- [ ] Created `terraform.tfvars` from `terraform.tfvars.example` with your values
- [ ] Decided on ECR image strategy (Option A, B, or C)
- [ ] Verified Bedrock model access
- [ ] Verified `backend.config` and `terraform.tfvars` are in `.gitignore`

## Running Terraform

Once all prerequisites are complete:

```bash
cd terraform

# Initialize Terraform with backend configuration
# The -backend-config flag loads your backend.config file
terraform init -backend-config=backend.config

# Validate configuration
terraform validate

# See what will be created
terraform plan

# Apply the configuration
terraform apply
```

**Note**: You must use `-backend-config=backend.config` when running `terraform init`.

## Common Issues

### Issue: "bucket does not exist"
- Make sure the S3 bucket name in `backend.config` matches exactly what you created
- Verify the bucket is in the same region (us-east-1)
- Ensure you ran `terraform init -backend-config=backend.config`

### Issue: "table does not exist"
- Ensure the DynamoDB table name matches exactly: `ecs-rag-project-tflock`
- Verify the table is in us-east-1

### Issue: "AccessDenied" errors
- Double-check all 9 IAM policies are attached to your SageMaker role
- Verify the backend access policy is also attached
- Wait a few minutes for IAM policy changes to propagate

### Issue: ECS tasks fail to start - "CannotPullContainerError"
- Verify ECR repositories exist and contain images
- Check ECS task execution role has ECR pull permissions (created by Terraform)
- Verify VPC endpoints for ECR are working

### Issue: "InvalidParameterException: CodeStar Connection"
- Verify the CodeStar connection is in "Available" state
- Ensure the connection ARN is correct in `terraform.tfvars`
- The connection must be in the same region (us-east-1)

### Security Reminder
- Never commit `backend.config` or `terraform.tfvars` to version control
- These files are already in `.gitignore`
- Always use the `.example` files as templates for team members
