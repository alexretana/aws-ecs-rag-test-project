variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ecs-rag"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "ragadmin"
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "ragdb"
}

variable "github_repo" {
  description = "GitHub repository for CodePipeline (format: owner/repo)"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch to track"
  type        = string
  default     = "main"
}

variable "codestar_connection_arn" {
  description = "ARN of CodeStar connection for GitHub"
  type        = string
}