# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${var.project_name}-${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-${var.environment}-logs"
  }
}

# X-Ray Sampling Rule
resource "aws_xray_sampling_rule" "main" {
  rule_name      = "${var.project_name}-${var.environment}-sampling"
  priority       = 1000
  version        = 1
  reservoir_size = 5
  fixed_rate     = 0.1  # 10% sampling
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"

  attributes = {}
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "ECS Service CPU Utilization"
          region = var.aws_region
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "${var.project_name}-${var.environment}-backend-service", "ClusterName", "${var.project_name}-${var.environment}-cluster"],
            ["AWS/ECS", "CPUUtilization", "ServiceName", "${var.project_name}-${var.environment}-frontend-service", "ClusterName", "${var.project_name}-${var.environment}-cluster"]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "ECS Service Memory Utilization"
          region = var.aws_region
          metrics = [
            ["AWS/ECS", "MemoryUtilization", "ServiceName", "${var.project_name}-${var.environment}-backend-service", "ClusterName", "${var.project_name}-${var.environment}-cluster"],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", "${var.project_name}-${var.environment}-frontend-service", "ClusterName", "${var.project_name}-${var.environment}-cluster"]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "ALB Request Count"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "${var.project_name}-${var.environment}-alb"]
          ]
          period = 60
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "ALB Response Times"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "${var.project_name}-${var.environment}-alb"]
          ]
          period = 60
          stat   = "Average"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 24
        height = 6
        properties = {
          title  = "Application Logs"
          region = var.aws_region
          query  = "SOURCE '/ecs/${var.project_name}-${var.environment}' | fields @timestamp, @message | sort @timestamp desc | limit 100"
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "backend_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-backend-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Backend CPU utilization is too high"

  dimensions = {
    ClusterName = "${var.project_name}-${var.environment}-cluster"
    ServiceName = "${var.project_name}-${var.environment}-backend-service"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-cpu-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "backend_memory_high" {
  alarm_name          = "${var.project_name}-${var.environment}-backend-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Backend memory utilization is too high"

  dimensions = {
    ClusterName = "${var.project_name}-${var.environment}-cluster"
    ServiceName = "${var.project_name}-${var.environment}-backend-service"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-memory-alarm"
  }
}