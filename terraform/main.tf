data "aws_caller_identity" "current" {}

module "vpc" {
  source = "./modules/vpc"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  aws_region         = var.aws_region
}

module "security" {
  source = "./modules/security"

  project_name = var.project_name
  environment  = var.environment
}

module "rds" {
  source = "./modules/rds"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  db_username         = var.db_username
  db_name             = var.db_name
  ecs_security_group_id = module.ecs.ecs_security_group_id

  depends_on = [module.vpc]
}

module "alb" {
  source = "./modules/alb"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids

  depends_on = [module.vpc]
}

module "monitoring" {
  source = "./modules/monitoring"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
}

module "ecs" {
  source = "./modules/ecs"

  project_name              = var.project_name
  environment               = var.environment
  aws_region                = var.aws_region
  vpc_id                    = module.vpc.vpc_id
  private_subnet_ids        = module.vpc.private_subnet_ids
  alb_security_group_id     = module.alb.security_group_id
  backend_target_group_arn  = module.alb.backend_target_group_arn
  frontend_target_group_arn = module.alb.frontend_target_group_arn
  db_secret_arn             = module.rds.secret_arn
  log_group_name            = module.monitoring.log_group_name
  xray_sampling_rule_name   = module.monitoring.xray_sampling_rule_name

  depends_on = [module.vpc, module.alb, module.rds, module.monitoring]
}

module "codepipeline" {
  source = "./modules/codepipeline"

  project_name                  = var.project_name
  environment                   = var.environment
  aws_region                    = var.aws_region
  account_id                    = data.aws_caller_identity.current.account_id
  github_repo                   = var.github_repo
  github_branch                 = var.github_branch
  codestar_connection_arn       = var.codestar_connection_arn
  backend_ecr_repository_url    = module.ecs.backend_ecr_repository_url
  frontend_ecr_repository_url   = module.ecs.frontend_ecr_repository_url
  ecs_cluster_name              = module.ecs.cluster_name
  backend_service_name          = module.ecs.backend_service_name
  frontend_service_name         = module.ecs.frontend_service_name
  backend_target_group_name     = module.alb.backend_target_group_name
  frontend_target_group_name    = module.alb.frontend_target_group_name
  backend_target_group_blue_name  = module.alb.backend_target_group_blue_name
  frontend_target_group_blue_name = module.alb.frontend_target_group_blue_name
  alb_listener_arn              = module.alb.listener_arn
  backend_listener_rule_arn     = module.alb.backend_listener_rule_arn
  frontend_listener_rule_arn    = module.alb.frontend_listener_rule_arn

  depends_on = [module.ecs, module.alb]
}