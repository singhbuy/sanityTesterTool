variable "aws_region" {
  description = "AWS region to provision the evidence store and secrets in."
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Globally-unique name for the evidence (screenshot/video/log) bucket. design.md §2.3."
  type        = string
}

variable "evidence_retention_days" {
  description = "Default retention window for run evidence before expiry. design.md §2.3/§4: 90 days default, configurable."
  type        = number
  default     = 90
}

variable "non_prod_environments" {
  description = <<-EOT
    Allow-listed values for RunConfig.environment (design.md §3). The Run
    Orchestrator validates against this list before applying any
    precondition — "prod"/"production" must never appear here
    (Req4 AC7, constitution #6).
  EOT
  type    = list(string)
  default = ["staging", "non-prod-qa", "non-prod-perf"]

  validation {
    condition     = !contains([for e in var.non_prod_environments : lower(e)], "prod") && !contains([for e in var.non_prod_environments : lower(e)], "production")
    error_message = "non_prod_environments must never include prod/production (Req4 AC7)."
  }
}

variable "service_account_name" {
  description = "Name for the least-privilege IAM role used by the automation service to read Xray/Jira creds and write evidence. design.md §2.8."
  type        = string
  default     = "sanity-tester-automation"
}
