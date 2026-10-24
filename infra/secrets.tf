# Secrets storage + least-privilege AWS-side access for the Xray Cloud REST
# API credential pair. design.md §2.8: client_id/client_secret, tied to a
# dedicated Jira service-account user scoped (in Jira Admin, not here) to
# test-execution-import + issue-create/attach only. client_secret does not
# auto-expire, so it needs the rotation policy noted in the secret's
# description — rotation itself is an operational task, not automated here.

resource "aws_secretsmanager_secret" "xray_jira_credentials" {
  name        = "sanity-tester/xray-jira-credentials"
  description = "Xray Cloud API client_id/client_secret for the sanity-tester automation service account. Rotate client_secret manually (it has no auto-expiry) — see design.md §2.8."
}

# Placeholder only — Terraform provisions the container, never a real
# credential. Populate the actual value out-of-band after creating the
# Jira service-account API key pair (Jira Admin > Apps > Xray Settings >
# API Keys), then this resource becomes a no-op on subsequent applies.
resource "aws_secretsmanager_secret_version" "xray_jira_credentials" {
  secret_id = aws_secretsmanager_secret.xray_jira_credentials.id
  secret_string = jsonencode({
    client_id     = "REPLACE_ME"
    client_secret = "REPLACE_ME"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Least-privilege role for the automation service: read this one secret,
# read/write only under the evidence bucket. No Jira-admin-equivalent AWS
# permission, no access to any other secret or bucket.
resource "aws_iam_role" "automation_service" {
  name = var.service_account_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "ecs-tasks.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "automation_service" {
  name = "${var.service_account_name}-least-privilege"
  role = aws_iam_role.automation_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadXrayJiraCredential"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.xray_jira_credentials.arn
      },
      {
        Sid    = "ReadWriteEvidenceBucket"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
        ]
        Resource = "${aws_s3_bucket.evidence.arn}/*"
      }
    ]
  })
}
