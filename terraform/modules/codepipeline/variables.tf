variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "account_id" {
  type = string
}

variable "github_repo" {
  type = string
}

variable "github_branch" {
  type = string
}

variable "codestar_connection_arn" {
  type = string
}

variable "backend_ecr_repository_url" {
  type = string
}

variable "frontend_ecr_repository_url" {
  type = string
}

variable "ecs_cluster_name" {
  type = string
}

variable "backend_service_name" {
  type = string
}

variable "frontend_service_name" {
  type = string
}

variable "backend_target_group_name" {
  type = string
}

variable "frontend_target_group_name" {
  type = string
}

variable "backend_target_group_blue_name" {
  type = string
}

variable "frontend_target_group_blue_name" {
  type = string
}

variable "alb_listener_arn" {
  type = string
}

variable "backend_listener_rule_arn" {
  type = string
}

variable "frontend_listener_rule_arn" {
  type = string
}