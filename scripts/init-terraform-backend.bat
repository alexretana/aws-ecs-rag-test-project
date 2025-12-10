@echo off
setlocal enabledelayedexpansion

set PROJECT_NAME=ecs-rag-project
set REGION=us-east-1

rem Get AWS account ID
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i

rem Create S3 bucket for Terraform state
set BUCKET_NAME=%PROJECT_NAME%-tfstate-%ACCOUNT_ID%
echo Creating S3 bucket: %BUCKET_NAME%
aws s3api create-bucket --bucket %BUCKET_NAME% --region %REGION%
if %errorlevel% neq 0 exit /b %errorlevel%

rem Enable versioning
echo Enabling versioning...
aws s3api put-bucket-versioning --bucket %BUCKET_NAME% --versioning-configuration Status=Enabled
if %errorlevel% neq 0 exit /b %errorlevel%

rem Enable encryption
echo Enabling encryption...
aws s3api put-bucket-encryption --bucket %BUCKET_NAME% --server-side-encryption-configuration "{\"Rules\": [{\"ApplyServerSideEncryptionByDefault\": {\"SSEAlgorithm\": \"aws:kms\"}}]}"
if %errorlevel% neq 0 exit /b %errorlevel%

rem Block public access
echo Blocking public access...
aws s3api put-public-access-block --bucket %BUCKET_NAME% --public-access-block-configuration "{\"BlockPublicAcls\": true, \"IgnorePublicAcls\": true, \"BlockPublicPolicy\": true, \"RestrictPublicBuckets\": true}"
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo Terraform backend created successfully:
echo   S3 Bucket: %BUCKET_NAME%
echo   Region: %REGION%
echo.
echo Note: State locking will use S3-based lockfiles (.tflock)
echo       No DynamoDB table is required with use_lockfile=true

endlocal