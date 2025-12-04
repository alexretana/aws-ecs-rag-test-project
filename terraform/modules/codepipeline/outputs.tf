output "pipeline_name" {
  value = aws_codepipeline.main.name
}

output "codebuild_project_name" {
  value = aws_codebuild_project.main.name
}

output "artifact_bucket" {
  value = aws_s3_bucket.codepipeline.bucket
}