output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "alb_arn" {
  value = aws_lb.main.arn
}

output "security_group_id" {
  value = aws_security_group.alb.id
}

output "backend_target_group_arn" {
  value = aws_lb_target_group.backend_green.arn
}

output "frontend_target_group_arn" {
  value = aws_lb_target_group.frontend_green.arn
}

output "backend_target_group_name" {
  value = aws_lb_target_group.backend_green.name
}

output "frontend_target_group_name" {
  value = aws_lb_target_group.frontend_green.name
}

output "backend_target_group_blue_name" {
  value = aws_lb_target_group.backend_blue.name
}

output "frontend_target_group_blue_name" {
  value = aws_lb_target_group.frontend_blue.name
}

output "listener_arn" {
  value = aws_lb_listener.http.arn
}

output "backend_listener_rule_arn" {
  value = aws_lb_listener_rule.backend.arn
}

output "frontend_listener_rule_arn" {
  value = aws_lb_listener_rule.frontend.arn
}