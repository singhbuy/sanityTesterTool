# Evidence Writer's object store. design.md §2.3:
# screenshots, full-run video, device/app logs; keyed by
# {xray_test_id}/{build_number}/{run_id}/..., accessed only via signed URLs
# attached to Xray/Jira (never public, never inlined as an attachment).

resource "aws_s3_bucket" "evidence" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_public_access_block" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  rule {
    id     = "expire-after-retention-window"
    status = "Enabled"

    expiration {
      days = var.evidence_retention_days
    }
  }
}

# Deny any non-TLS access — signed URLs are the only intended access path.
resource "aws_s3_bucket_policy" "evidence_require_tls" {
  bucket = aws_s3_bucket.evidence.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.evidence.arn,
          "${aws_s3_bucket.evidence.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
