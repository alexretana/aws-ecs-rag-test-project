variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "backend_target_group_arn" {
  type = string
}

variable "frontend_target_group_arn" {
  type = string
}

variable "db_secret_arn" {
  type = string
}

variable "rds_security_group_id" {
  type = string
}

variable "log_group_name" {
  type = string
}

variable "xray_sampling_rule_name" {
  type = string
}