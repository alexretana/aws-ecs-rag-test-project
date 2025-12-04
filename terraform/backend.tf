terraform {
  backend "s3" {
    bucket         = "ecs-rag-project-tfstate-${data.aws_caller_identity.current.account_id}"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ecs-rag-project-tflock"
    encrypt        = true
  }
}