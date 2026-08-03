# CloudFront in front of the ALB provides an HTTPS URL without needing a
# custom domain + ACM certificate. Google OAuth rejects plain-HTTP redirect
# URIs, so the app must be served over HTTPS.

resource "aws_cloudfront_distribution" "main" {
  count           = var.enable_cloudfront ? 1 : 0
  enabled         = true
  is_ipv6_enabled = true
  comment         = "${local.name_prefix} — HTTPS entry point"
  price_class     = "PriceClass_200" # includes Asia

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      origin_read_timeout    = 60
    }
  }

  default_cache_behavior {
    target_origin_id       = "alb"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]

    # Dynamic app: no caching, forward everything (cookies, headers, query).
    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # Managed-CachingDisabled
    origin_request_policy_id = "216adef6-5c7f-47e4-b989-5492eafa07d3" # Managed-AllViewer
  }

  # Cache Next.js static assets aggressively.
  ordered_cache_behavior {
    path_pattern           = "/_next/static/*"
    target_origin_id       = "alb"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]

    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # Managed-CachingOptimized
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = { Name = "${local.name_prefix}-cdn" }
}

locals {
  # Falls back to plain-HTTP ALB when CloudFront is disabled. Google OAuth
  # will refuse a non-HTTPS redirect URI, so sign-in only works once
  # enable_cloudfront = true.
  public_url = var.enable_cloudfront ? "https://${aws_cloudfront_distribution.main[0].domain_name}" : "http://${aws_lb.main.dns_name}"
}
