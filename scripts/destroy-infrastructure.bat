@echo off
setlocal enabledelayedexpansion

echo === ECS RAG Project Infrastructure Destruction ===
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
    echo Cannot proceed without backend configuration.
    exit /b 1
)

rem Initialize Terraform with backend config
echo Initializing Terraform with backend configuration...
terraform init -backend-config=backend.config -reconfigure
if %errorlevel% neq 0 (
    echo ERROR: Terraform init failed
    exit /b 1
)

echo.
echo === WARNING: Infrastructure Destruction ===
echo.
echo This will DESTROY all infrastructure including:
echo   - ECS clusters and services
echo   - RDS database instances
echo   - Application Load Balancer
echo   - VPC and networking resources
echo   - ECR repositories (images will be deleted)
echo   - CodePipeline and associated resources
echo   - CloudWatch logs and monitoring
echo   - Security groups and IAM roles
echo.
echo This action is IRREVERSIBLE and will result in DATA LOSS!
echo.

set /p CONFIRM1="Are you absolutely sure you want to destroy ALL infrastructure? (yes/NO): "
if /i not "%CONFIRM1%"=="yes" (
    echo Destruction cancelled.
    exit /b 0
)

rem Show Terraform destroy plan for confirmation
echo.
echo Generating Terraform destroy plan...
echo This will show all resources that will be destroyed...
echo.

terraform plan -destroy -out=tfdestroy
if %errorlevel% neq 0 (
    echo ERROR: Terraform destroy plan failed
    exit /b 1
)

echo.
echo === Terraform Destroy Plan Complete ===
echo.
echo Please review the plan above carefully.
echo All listed resources will be PERMANENTLY DESTROYED.
echo.

set /p CONFIRM2="Type 'destroy' to proceed with destruction: "
if /i not "%CONFIRM2%"=="destroy" (
    echo Destruction cancelled.
    echo Cleaning up plan file...
    del /f /q tfdestroy 2>nul
    exit /b 0
)

rem Apply Terraform destroy using saved plan
echo.
echo Running Terraform destroy with saved plan...
echo This may take several minutes...
echo.

terraform apply tfdestroy
if %errorlevel% neq 0 (
    echo ERROR: Terraform destroy failed
    del /f /q tfdestroy 2>nul
    exit /b 1
)

rem Clean up plan file
echo.
echo Cleaning up plan file...
del /f /q tfdestroy 2>nul

echo.
echo === Infrastructure Destruction Complete ===
echo.
echo All Terraform-managed resources have been destroyed.
echo.
echo Note: The following resources are NOT destroyed by this script:
echo   - S3 bucket for Terraform state
echo   - Any manually created resources outside of Terraform
echo.
echo If you want to completely clean up, you may manually delete:
echo   1. The Terraform state S3 bucket
echo   2. Any remaining CloudWatch log groups
echo   3. Any ECR images that were protected from deletion

cd ..
endlocal