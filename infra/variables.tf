variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "sentellent"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "sentellent"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "sentellent_admin"
  sensitive   = true
}

variable "backend_cpu" {
  description = "Backend task CPU units"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Backend task memory (MiB)"
  type        = number
  default     = 1024
}

variable "frontend_cpu" {
  description = "Frontend task CPU units"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Frontend task memory (MiB)"
  type        = number
  default     = 512
}

variable "backend_desired_count" {
  description = "Number of backend tasks"
  type        = number
  default     = 1
}

variable "frontend_desired_count" {
  description = "Number of frontend tasks"
  type        = number
  default     = 1
}

variable "domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}

variable "enable_cloudfront" {
  description = <<-EOT
    Create the CloudFront distribution that fronts the ALB with HTTPS.
    New AWS accounts must be verified by AWS Support before they may create
    distributions; until then set this to false so the rest of the stack can
    deploy. Google OAuth requires an HTTPS redirect URI, so this must be true
    for production sign-in to work.
  EOT
  type        = bool
  default     = false
}

variable "public_url_override" {
  description = <<-EOT
    Public HTTPS origin users hit, when it is not CloudFront. Set this when the
    frontend is hosted externally (e.g. Vercel) and proxies /api/* back to the
    ALB. It drives CORS_ORIGINS, FRONTEND_URL and GOOGLE_REDIRECT_URI on the
    backend task. Leave empty to use CloudFront (or the raw ALB) instead.
  EOT
  type        = string
  default     = ""
}
