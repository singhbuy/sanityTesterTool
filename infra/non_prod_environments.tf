# Authoritative allow-list for RunConfig.environment (design.md §3, Req4
# AC7). The Run Orchestrator reads this at runtime and rejects any
# RunConfig whose environment isn't on it, before applying any
# precondition. This does NOT provision the actual non-prod game
# environment(s) named here — that's the game's own infra, out of scope
# for this repo (see infra/README.md).

resource "aws_ssm_parameter" "non_prod_environments" {
  name        = "/sanity-tester/non-prod-environments"
  description = "Allow-listed environment names for RunConfig.environment. Never contains prod/production — enforced by variables.tf's validation block."
  type        = "StringList"
  value       = join(",", var.non_prod_environments)
}
