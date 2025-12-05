@echo off
setlocal enabledelayedexpansion

rem Script to create and attach IAM policies to a SageMaker execution role
rem Usage: apply-policies.bat <role-name>

if "%~1"=="" (
    echo Usage: %~nx0 ^<role-name^>
    echo Example: %~nx0 my-sagemaker-execution-role
    exit /b 1
)

set ROLE_NAME=%~1
set SCRIPT_DIR=%~dp0

rem Get AWS account ID
echo Getting AWS account ID...
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
echo Account ID: %ACCOUNT_ID%

rem Verify role exists
echo Verifying role exists: %ROLE_NAME%
aws iam get-role --role-name "%ROLE_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Role '%ROLE_NAME%' does not exist
    exit /b 1
)

echo Processing policy files...

rem Create and attach each policy
for %%f in ("%SCRIPT_DIR%*.json") do (
    set policy_file=%%f
    set policy_basename=%%~nf
    set policy_name=SageMaker-ECS-RAG-!policy_basename!

    echo.
    echo Processing: !policy_basename!

    rem Try to create the policy
    for /f "tokens=*" %%i in ('aws iam create-policy --policy-name "!policy_name!" --policy-document "file://!policy_file!" --description "IAM policy for ECS RAG Terraform deployment - !policy_basename!" --query Policy.Arn --output text 2^>nul') do set policy_arn=%%i

    rem If policy already exists, get its ARN
    if "!policy_arn!"=="" (
        echo   Policy already exists, getting ARN...
        set policy_arn=arn:aws:iam::%ACCOUNT_ID%:policy/!policy_name!
    ) else (
        echo   Created policy: !policy_name!
    )

    rem Attach the policy to the role
    aws iam attach-role-policy --role-name "%ROLE_NAME%" --policy-arn "!policy_arn!" >nul 2>&1
    if %errorlevel% equ 0 (
        echo   ✓ Attached: !policy_name!
    ) else (
        echo   ℹ Already attached: !policy_name!
    )
)

echo.
echo ================================================
echo Policy application complete!
echo ================================================
echo.
echo Attached policies:
aws iam list-attached-role-policies --role-name "%ROLE_NAME%" --query "AttachedPolicies[?contains(PolicyName, 'ECS-RAG')].PolicyName" --output table

echo.
echo Next steps:
echo 1. Review PREREQUISITES.md for remaining setup tasks
echo 2. Create Terraform backend (S3 bucket + DynamoDB table)
echo 3. Set up CodeStar connection to GitHub
echo 4. Create terraform.tfvars with your configuration
echo 5. Run: cd terraform ^&^& terraform init ^&^& terraform plan

endlocal