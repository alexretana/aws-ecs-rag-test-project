output "log_group_name" {
  value = aws_cloudwatch_log_group.main.name
}

output "log_group_arn" {
  value = aws_cloudwatch_log_group.main.arn
}

output "xray_sampling_rule_name" {
  value = aws_xray_sampling_rule.main.rule_name
}

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.main.dashboard_name
}