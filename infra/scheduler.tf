# Nightly news + fundamentals refresh for all followed tickers.
# EventBridge Scheduler launches a one-off Fargate task running
# `python -m app.jobs.refresh` on the backend image. Ingestion is idempotent
# (advisory locks + content-hash dedup), so overlap with user-triggered
# ingestion is safe.

resource "aws_iam_role" "scheduler" {
  name = "${local.name_prefix}-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler" {
  name = "${local.name_prefix}-scheduler-policy"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecs:RunTask"]
        Resource = "*"
        Condition = {
          ArnEquals = { "ecs:cluster" = aws_ecs_cluster.main.arn }
        }
      },
      {
        Effect = "Allow"
        Action = ["iam:PassRole"]
        Resource = [
          aws_iam_role.ecs_task_execution.arn,
          aws_iam_role.ecs_task.arn,
        ]
      }
    ]
  })
}

resource "aws_scheduler_schedule" "news_refresh" {
  name       = "${local.name_prefix}-news-refresh"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  # 02:00 IST daily (20:30 UTC), before Indian market pre-open.
  schedule_expression          = "cron(30 20 * * ? *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.scheduler.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.backend.arn
      launch_type         = "FARGATE"
      task_count          = 1

      network_configuration {
        # Public subnet + public IP: the refresh job needs outbound internet
        # (RSS feeds, yfinance, OpenAI) and there is no NAT Gateway.
        subnets          = aws_subnet.public[*].id
        security_groups  = [aws_security_group.ecs.id]
        assign_public_ip = true
      }
    }

    input = jsonencode({
      containerOverrides = [{
        name    = "backend"
        command = ["python", "-m", "app.jobs.refresh"]
      }]
    })

    retry_policy {
      maximum_retry_attempts = 1
    }
  }
}
