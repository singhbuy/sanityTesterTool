# Infra: Xray/Jira Game Sanity Test Automation

Implements the infra items from [design.md](../specs/design.md) §2.3, §2.8, and §4
(Non-functional mapping), owned by devops per the blackboard build-order breakdown.

## Scope

| Design.md item | File | Status |
|---|---|---|
| Evidence Writer's S3-compatible store + 90d retention (§2.3) | `evidence_store.tf` | Ready to apply |
| Secrets manager + least-privilege service account for Xray Cloud API creds (§2.8) | `secrets.tf` | Ready to apply (secret *value* must be populated out-of-band after the Jira-side service account is created) |
| Non-prod/staging environment allow-list for the `RunConfig.environment` field (§3) | `non_prod_environments.tf` | Config only — see note below |
| PC Execution Engine runner (§2.2: Playwright, mandatory for PC) | `execution-runner/` | Scaffolding — Dockerfile ready, app code pending build-order step 3 |

## Device/execution-farm sizing (device-platform infra, not storage/secrets)

Revised as of the PixiJS/WebGL engine swap (requirements.md v1.4, design.md v6):

- **PC**: no device farm at all — just the `execution-runner/` container run
  in CI, same as any other browser-automation job. Final, not gated on
  anything below.
- **Mobile**: still a 2-way open choice, gated on the Step-0 spike (design.md
  §5 item 1): (a) Appium WebView-context — reuses the same
  BrowserStack/AWS-Device-Farm-speaks-Appium grid already flagged as the
  path of least resistance in the original engine research, so sizing here
  is mostly "pick a vendor, same shape as any Appium-based mobile farm"; or
  (b) Drizz narrowed to mobile-only — its managed device cloud, if it clears
  the Step-0 spike, could absorb this sizing question entirely instead.
  Not provisioning either until the spike (and real build/staging access,
  currently blocked — see blackboard) resolves which one.

## Explicitly out of scope here

The **actual staging/non-prod game environment** that test runs execute
against (Req4 AC7: "never prod") is the game's own infrastructure, not this
tool's. This repo only owns the allow-list of environment *names* the Run
Orchestrator validates `RunConfig.environment` against before applying any
precondition (design.md §3: "`environment` is validated against an
allow-list at the Orchestrator before any precondition is applied"). Standing
up the actual non-prod game environment is a separate, game-infra-owned task.

## Assumptions / open choices

- **AWS is the reference implementation.** design.md deliberately left the
  object store "S3-compatible" and the secret store "a secrets manager"
  generic. Terraform + AWS S3 + AWS Secrets Manager is the concrete default
  here; swap `evidence_store.tf`/`secrets.tf` for GCS/Azure Blob/Vault
  equivalents if the org standardizes elsewhere — nothing downstream
  (Evidence Writer, Xray/Jira Client) is AWS-specific by design, they consume
  a bucket name + a secret ARN/path.
- **No live cloud account is configured in this environment** (no AWS CLI,
  no credentials, confirmed before writing this). These files are `plan`-able
  once pointed at a real account/region via `variables.tf`, not yet applied.
- Jira-side least-privilege (scoping the service-account *Jira user* to
  test-execution-import + issue-create/attach only) happens in Jira Admin,
  not here — Terraform only scopes the AWS-side credential storage/IAM
  around it. See `secrets.tf` comments.

## Apply

```sh
cd infra
terraform init
terraform plan -var="bucket_name=<org-specific-bucket>" -var="aws_region=<region>"
terraform apply
```

After apply, populate the Secrets Manager secret value (`client_id` /
`client_secret` from Jira Admin > Apps > Xray Settings > API Keys) out of
band — Terraform provisions the secret container and access policy, never a
real credential value.
