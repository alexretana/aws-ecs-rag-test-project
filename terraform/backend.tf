terraform {
  backend "s3" {
    # Backend configuration is provided via backend.config file
    # This avoids hardcoding sensitive information in version control
    # Run: terraform init -backend-config=backend.config
    key     = "terraform.tfstate"
    encrypt = true
  }
}