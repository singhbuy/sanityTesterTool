---
name: git-workflow
description: Git branching and PR policy for this multi-agent team (pm, dev, qa, ux, devops) sharing one local clone. Use this before running any git commit or git push in this project — it governs who may push, where, and how changes reach main/production.
---

# Team git workflow

All peer agents in this project (pm, dev, qa, ux, devops — see `blackboard/registry.md`) share one local clone. This skill is the policy for how a change made by any of them ends up on `main`. It supersedes ad-hoc pushing — e.g. `dev` pushing landing-page commits straight to `origin/main` was the old pattern; it is not the pattern anymore.

## The rule, in order

1. **Any agent, after finishing a change**: `git add` the files you own, then `git commit` locally. **Do not run `git push`.** Ever. No exceptions for "it's a small fix."
2. **devops is the only agent that pushes**, and only to the `dev` branch (`git push origin dev`). Nobody else pushes to `dev`, `main`, or anything else.
3. **devops runs tests** against what's accumulated on `dev` before doing anything else with it.
4. **devops opens a PR from `dev` into `main`** (e.g. `gh pr create --base main --head dev`) once tests pass — and only once they pass.
5. **The human approves and merges the PR.** Not devops, not any agent. If an agent thinks a PR is urgent, say so on the blackboard — don't merge around the human.
6. **Merging to `main` is the deploy trigger.** The product deploys from `main`; `dev` and any other branch are never deploy sources.

## What this looks like in practice

- Finish a task → `git commit` locally → log it on the blackboard as `done` (as always) → stop. You're not responsible for anything past your own commit.
- Need something to ship sooner? Flag it to `devops` on the blackboard with why — don't push to work around the queue.
- `devops`: periodically collect local commits (they're already in the shared clone — no one else has pushed them anywhere), push to `origin/dev`, run tests, open the PR, and post the PR link on the blackboard so the human can review it. If tests fail, say so on the blackboard and hold the PR — don't open it red.
- Everyone else: never run `git push`, never merge a PR, never commit directly to `main` once `dev` exists as the working branch.

## Why this shape

One pusher means no two agents race on `git push` or silently bypass tests before `main` moves — load-bearing because this team doesn't have separate clones or CI gating pushes for them automatically. A single tested integration branch (`dev`) plus a human-gated PR into `main` is the cheapest version of trunk-based-with-a-gate that works when everyone shares one working directory.
