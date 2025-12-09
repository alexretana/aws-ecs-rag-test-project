@echo off
setlocal enabledelayedexpansion

echo === ECS RAG Project Deployment with Initial ECR Images ===
echo.

rem Check if Docker is installed and running
echo Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed. Please install Docker before running this script.
    exit /b 1
)

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker before running this script.
    exit /b 1
)

echo ✓ Docker is installed and running
echo.

rem Check if AWS CLI is installed
echo Checking AWS CLI installation...
aws --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: AWS CLI is not installed. Please install AWS CLI before running this script.
    exit /b 1
)

echo ✓ AWS CLI is installed
echo.

rem Check if Terraform is installed
echo Checking Terraform installation...
terraform version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Terraform is not installed. Please install Terraform before running this script.
    exit /b 1
)

echo ✓ Terraform is installed
echo.

rem Check AWS credentials
echo Checking AWS credentials...
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: AWS credentials are not configured. Please run 'aws configure' or set up environment variables.
    exit /b 1
)

echo ✓ AWS credentials are configured
echo.

rem Change to terraform directory
cd terraform
if %errorlevel% neq 0 (
    echo ERROR: Could not change to terraform directory
    exit /b 1
)

rem Check if backend.config exists
if not exist "backend.config" (
    echo ERROR: backend.config file not found in terraform directory
    echo.
    echo Please follow these steps first:
    echo 1. Run scripts\init-terraform-backend.bat to create the S3 bucket and DynamoDB table
    echo 2. Copy backend.config.example to backend.config
    echo 3. Update backend.config with your AWS account ID
    echo 4. Run this script again
    exit /b 1
)

rem Initialize Terraform with backend config
echo Initializing Terraform with backend configuration...
terraform init -backend-config=backend.config
if %errorlevel% neq 0 (
    echo ERROR: Terraform init failed
    exit /b 1
)

echo.
echo === Starting Deployment ===
echo.
echo This deployment will:
echo 1. Create all infrastructure including ECR repositories
echo 2. Automatically push placeholder images to ECR
echo 3. Deploy ECS services with the placeholder images
echo 4. Set up CodePipeline for future deployments
echo.

set /p CONTINUE="Do you want to continue? (y/N): "
if /i not "%CONTINUE%"=="y" (
    echo Deployment cancelled.
    exit /b 0
)

rem Show Terraform plan for confirmation
echo.
echo Generating Terraform plan...
echo This will show all resources that will be created...
echo.

terraform plan -out=tfplan
if %errorlevel% neq 0 (
    echo ERROR: Terraform plan failed
    exit /b 1
)

echo.
echo === Terraform Plan Complete ===
echo.
echo Please review the plan above carefully.
echo This deployment will:
echo 1. Create all infrastructure including ECR repositories
echo 2. Automatically push placeholder images to ECR
echo 3. Deploy ECS services with the placeholder images
echo 4. Set up CodePipeline for future deployments
echo.

set /p APPLY="Do you want to proceed with applying this plan? (y/N): "
if /i not "%APPLY%"=="y" (
    echo Deployment cancelled.
    echo Cleaning up plan file...
    del /f /q tfplan 2>nul
    exit /b 0
)

rem Apply Terraform using saved plan
echo.
echo Running Terraform apply with saved plan...
echo This will take some time as it creates all resources and pushes images...
echo.

terraform apply tfplan
if %errorlevel% neq 0 (
    echo ERROR: Terraform apply failed
    del /f /q tfplan 2>nul
    exit /b 1
)

rem Clean up plan file
echo.
echo Cleaning up plan file...
del /f /q tfplan 2>nul

echo.
echo === Deployment Complete ===
echo.
echo Your ECS RAG application has been deployed with placeholder images.
echo.
echo Next steps:
echo 1. Build your actual application images
echo 2. Push them to the ECR repositories
echo 3. Trigger a new deployment via CodePipeline
echo.
echo ECR Repository URLs:
for /f "tokens=*" %%i in ('terraform output -raw backend_ecr_repository_url 2^>nul') do echo Backend: %%i
for /f "tokens=*" %%i in ('terraform output -raw frontend_ecr_repository_url 2^>nul') do echo Frontend: %%i
echo.
echo Load Balancer URL:
for /f "tokens=*" %%i in ('terraform output -raw alb_dns_name 2^>nul') do echo Application: %%i
if %errorlevel% neq 0 (
    echo Check Terraform outputs for ALB DNS name
)

cd ..
endlocal