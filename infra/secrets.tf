resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name                    = "${local.name_prefix}/anthropic-api-key"
  recovery_window_in_days = 0
  tags                    = { Name = "${local.name_prefix}-anthropic-key" }
}

resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${local.name_prefix}/openai-api-key"
  recovery_window_in_days = 0
  tags                    = { Name = "${local.name_prefix}-openai-key" }
}

resource "aws_secretsmanager_secret" "google_oauth" {
  name                    = "${local.name_prefix}/google-oauth"
  recovery_window_in_days = 0
  tags                    = { Name = "${local.name_prefix}-google-oauth" }
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${local.name_prefix}/jwt-secret"
  recovery_window_in_days = 0
  tags                    = { Name = "${local.name_prefix}-jwt-secret" }
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}
