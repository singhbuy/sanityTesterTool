# Design: Xray/Jira Game Sanity Test Automation

Status: **Draft v9** — implements [requirements.md v1.4](./requirements.md), governed by [constitution.md](./constitution.md).

This is a first pass covering architecture, data model, and the one remaining open risk (§5: confirming the Playwright/Appium + PixiJS scene-graph approach against a real build) called out in requirements.md. It is scoped to be reviewed on the blackboard before implementation starts.

**v9 changelog** (resolves @qa's obs on v8): `blocked:evidence_incomplete` was an orphaned enum value in v8 — not in the Grouper's trigger list (correctly) but also missing from the new Run Health list, so it had no dashboard routing at all. §2.6 and §1's diagram now include it in the Run Health list alongside `ambiguous`/`blocked:timeout`/`blocked:missing_precondition`, matching what ux-dashboard-spec.md already had.

**v8 changelog** (resolves @ux's obs on v7 + @qa's +1): §2.5 no longer triggers the Grouper on `ambiguous` — v7's new ambiguous-vs-failed:locator rule meant `ambiguous` is purely an authoring-gap signal, so grouping it into Jira-fileable candidate defects (the old trigger list) would misroute authoring problems as product bugs. `ambiguous` now gets the same "reported, not grouped, not Jira-fileable" treatment as `blocked:timeout`/`blocked:missing_precondition`, per Req2 AC3. §2.6 updated to match (Run Health list).

**v7 changelog** (resolves @qa's 2 obs on v6): §2.2 now gives one explicit rule for `ambiguous` (no target specified — authoring gap) vs. `failed:locator` (target specified, missing at runtime — real regression) instead of the old "failure/ambiguous" slash; §6's §3 row updated to match. §5 item 1 now explicitly includes testing Drizz's mobile-web/WebGL fit as sub-task (c), since §2.2's mobile (a)-Appium-vs-(b)-Drizz choice was gated on testing both but only (a)/(b)'s Playwright/Appium half had a tracked task.

**v6 changelog**: execution engine replaced per requirements.md v1.4 — the game renders via PixiJS/WebGL, not a native engine, which invalidated the Drizz/Airtest+Poco/AltTester+Appium research. §2.2 rewritten around Playwright (PC) + Appium WebView-context (mobile), both driving the PixiJS scene graph via its own official devtools hook (`@pixi/devtools` / `globalThis.__PIXI_APP__`) for object-level lookup and dynamic coordinate clicks/taps — no vendor self-healing to gate, so Req2 AC9 is satisfied structurally. §1 diagram, §5 item 1, and §6's §3 row updated to match.

**v5 changelog**: added a post-split re-matching rule to §2.5 (Candidate Defect Grouper) — per @ux's open item on the dashboard spec, design.md didn't say what happens when a later failure matches a grouping key that now spans more than one open group after a split.

**v4 changelog**: made the §2.1 precedence rule's scope explicit — it governs run-level aggregation across different steps, not only same-step retry+heal overlap — per @qa's Milestone 1 acceptance-test matrix (test cases 5/6/8 exercise cross-step aggregation that v3's wording didn't explicitly cover).

**v3 changelog**: product owner resolved both outstanding open questions (2026-10-24) — platform scope is mobile + PC only for v1 (console excluded, §3), and Jira edition is confirmed Cloud (§2.8, no PAT/DC variant needed). §5 open-items list trimmed accordingly.

**v2 changelog** (folding in @qa's 4 testability obs and @ux's 2 UX obs on v1, @devops's DC fact-check reply): added an explicit precedence rule for `ambiguous` vs `passed_after_retry` when both fire on the same step (§2.1, §2.4); added a 4th `blocked_reason` value for evidence-capture failure itself (§2.4); resolved the Drizz gate to a one-time engine-selection decision, not a per-case runtime fallback (§2.2); `device_id_or_pool` resolution now requires recording the specific resolved device in evidence (§3); added the precondition-preset editing surface (§2.6); added dismissed-candidate linking behavior in the Grouper (§2.5).

## 1. System overview

```
CI pipeline (post-build webhook)
        |
        v
  [Run Orchestrator] --reads--> [Config Store: stable subset, device/platform, precondition presets]
        |
        |--1. resolve run config (Req5 shared schema: device/platform + Req4 precondition preset)
        |--2. set preconditions on target env (Req4 AC1-3, AC7: non-prod/staging only)
        |
        v
  [Execution Engine]  (Playwright for PC, Appium WebView-context for mobile — see §2.2)
        |
        |--per step: screenshot, step result, ambiguity/precondition check (Req2)
        |--per run: full video, device/app logs, retry attempts (Req2 AC7-9)
        |
        v
  [Evidence Writer] --> S3-compatible object store (signed URLs, 90d retention default)
        |
        v
  [Result Processor]
        |--pass / fail / blocked:timeout / blocked:missing-precondition / blocked:setup / ambiguous
        |--"passed after retry" tagging (Req2 AC8)
        |
        |--on failed/blocked:setup --> [Candidate Defect Grouper] (Req3 AC1: test ID + step + root-cause category)
        |                                        |
        |                                        v
        |                              [Review Dashboard] (Req3 AC9, auth-gated)
        |                                queue view -> detail view -> approve/reject/split
        |                                        |
        |                                        | (human approval only)
        |                                        v
        |                              [Xray/Jira Client] --> Xray Cloud REST API
        |                                   (import execution result, attach evidence, file Jira bug)
        |
        |--on ambiguous/blocked:timeout/blocked:missing_precondition/blocked:evidence_incomplete --> dashboard "Run Health" list (reported, not grouped, no Jira action — §2.5/§2.6)
        |
        |--on pass --> [Xray/Jira Client] (import clean/retried execution result, linked to test case + build)
```

Every box above either reads from or writes to the Run Orchestrator's config/state so a run is reconstructible end to end from (test case ID, build number, device/platform, precondition preset, timestamp) — this is the traceability surface for constitution §5.

## 2. Components

### 2.1 Run Orchestrator
- Entry point for both triggers (Non-Functional: CI webhook primary, manual secondary).
- Resolves one run config object (§4) from: the CI payload (build number, environment, timestamp — Req1 AC5), the configured stable subset (Xray label `automation-stable`), and operator-selected device/platform + precondition preset (Req5 AC3 shared schema).
- Owns the state machine per test case run: `pending -> setting-preconditions -> executing -> {passed | passed-after-retry | ambiguous | failed | blocked:timeout | blocked:missing-precondition | blocked:setup | blocked:evidence-incomplete}`. No other component writes this status.
- Precondition failures (Req4 AC3) and timeouts (Req2 AC6) are caught here, not inferred by the execution engine — keeps constitution §1/§3's "never guess" boundary at the orchestrator, not scattered across engine-specific code.
- **Precedence rule (resolves @qa's obs on AC8 vs AC9 overlap)**: when a step both retries (Req2 AC7) and triggers engine self-heal/adaptation (Req2 AC9) before succeeding, the result is `ambiguous`, never `passed_after_retry`. Rationale: a plain retry means the same deterministic step eventually succeeded (flakiness); a self-heal means the engine changed what it was doing to make the step succeed (the step's resolvability is itself in question) — that is a strictly stronger "don't trust this as clean" signal than AC8's case, so AC9 outranks AC8 whenever both fire on the same step. Precedence order, highest wins: `ambiguous > blocked:* > passed_after_retry > failed > passed`.
- **Run-level aggregation (made explicit for @qa's Milestone 1 test matrix)**: a run has many steps, each with its own outcome; the run-level result is the highest-precedence outcome across *all* steps, using the same order above — not just when both conditions hit the same step. E.g. one step that's `passed_after_retry` plus a different step that hits `blocked:timeout` or carries a genuinely `ambiguous` step (Req2 AC1) yields a run-level result of `blocked:timeout` / `ambiguous` respectively, never `passed_after_retry`. This is the same rule applied at two scopes (single-step history vs. whole-run rollup), not two different rules.

### 2.2 Execution Engine (pluggable)
- Interface: `run_step(step) -> {status, screenshot, log_excerpt}`, `run_case(case) -> {video_ref, full_log_ref, step_results[]}`. Kept behind this interface so the PC/mobile driver choice below is swappable without touching the Orchestrator, Grouper, or Dashboard.
- **The game renders via PixiJS/WebGL** (confirmed by product owner, 2026-10-24) — a browser- or webview-hosted canvas, not a native Unity/Unreal/Godot binary. This ruled out the originally-researched engines: Airtest+Poco has no WebGL/PixiJS driver (only Android/iOS-native, Windows, Unity3D, cocos2d-x); AltTester+Appium is Unity-SDK-only; Maestro has no accessibility tree for a rendered canvas; and Drizz is a mobile-only platform (iOS/Android/mobile-web, no desktop browser support) that can't cover this component's PC target regardless of the canvas question.
- **PC driver: Playwright**, native browser automation — mandatory, no viable off-the-shelf alternative exists for PC (confirmed independently by @qa's parallel research). **Mobile driver: two live candidates, not yet decided**: (a) **Appium** WebView-context switching to get a ChromeDriver/webdriver session inside the game's webview wrapper (`driver.switch_to.context("WEBVIEW_...")` — not AltTester, which doesn't apply here) running the same scene-graph-hook technique as PC; or (b) **Drizz**, narrowed from "primary for everything" to "possible mobile-only candidate" since its vision-AI reads rendered pixels and may sidestep WebKit/mobile-Safari DOM quirks that affect (a)'s device-fidelity cost. Still gated on its own (now mobile-scoped) self-heal-signal verification. Pick between (a)/(b) once the Step-0 spike below runs on both.
- **Object-level introspection, both drivers, same technique**: the game exposes its live PixiJS scene graph via the engine's own official devtools hook — `globalThis.__PIXI_APP__ = app` (one line, the same mechanism the `@pixi/devtools` inspector uses) — enabled in QA/staging builds. The driver (Playwright `page.evaluate` / Appium's JS execution in the webview context) looks up the target object by id/name in the scene graph, reads its `boundingBox()` at runtime (never a hardcoded coordinate — the layout can legitimately move between builds), converts to canvas-relative coordinates, and dispatches a real pointer (Playwright `page.mouse.click`) or touch (Appium W3C actions) event at that point. This is the direct equivalent of Poco's object-level introspection, reimplemented for this game's actual stack — confirmed as an established pattern by non-vendor sources: an ASE 2022 academic paper and its published PixiJS visual-testing framework (`asgaardlab/canvas-visual-bugs-testbed`), and PixiJS's own first-party devtools package.
- **Req2 AC9 is satisfied structurally, not by a gate**: there is no vendor self-healing to detect or surface — object resolution is an exact scene-graph lookup. No self-heal-signal verification spike is needed for this engine choice (replaces the superseded Drizz spike — see §5).
- **`ambiguous` vs. `failed:locator` — one rule, not a slash (resolves @qa's obs on design.md v6)**: these are two different code paths with two different Req2 outcomes, decided on *when* the target was unresolvable, not just that it was:
  - **Step config never specifies a target object id/selector at all** → `ambiguous` (Req2 AC1). This is a static check the Orchestrator makes against the test case definition *before* attempting execution — an authoring defect ("the test case didn't say what to click"), not something the engine ever tries to resolve.
  - **Step config specifies a target object id, and the scene-graph lookup for that id returns nothing at runtime** (object missing or renamed) → `failed`, with `root_cause_category: locator` (the Req3 AC1 grouping key already has this category). The test case was authored correctly; the live object genuinely isn't where the test says it should be — a real, attributable regression signal, not an authoring gap, so it's eligible for the Grouper/Jira path, not just a "report separately from pass/fail" bucket.
  - Both are honest per constitution §1/§3 (neither is a silent pass), but only the second is a candidate defect — collapsing them into one "failure/ambiguous" event, as v6's §2.2/§6 text did, would misroute authoring defects into the defect-filing pipeline and vice versa.
- **Open implementation task, not yet resolved by this design**: confirm hands-on, against a real build, that (a) the game team can actually expose `globalThis.__PIXI_APP__` in QA/staging builds, and (b) Playwright/Appium can reliably drive pointer/touch events against the real canvas end-to-end on both PC and the mobile webview wrapper (§5 item 1).

### 2.3 Evidence Writer
- Writes screenshots (per verification step), one full-run video, and device/app logs to the S3-compatible store defined in Non-Functional Constraints, keyed by `{xray_test_id}/{build_number}/{run_id}/...`.
- Returns signed URLs (default 90-day expiry matching the retention window) that get attached to the Xray execution result and, if a candidate defect is filed, the Jira issue. Evidence is never inlined into Jira/Xray attachments directly (constitution §2 + Non-Functional).
- Retry attempts (Req2 AC7) are written as additional evidence entries under the same run, not overwritten — a "passed after retry" result's evidence trail shows every attempt, not just the last one.

### 2.4 Result Processor
- Pure function over an Execution Engine's raw step/run results -> one of the statuses in §2.1's state machine. This is where Req1 AC2/AC4/AC5 (evidence completeness) and Req2 AC1-2 (ambiguous step / unresolved precondition) are enforced as hard checks, not best-effort — a run missing required evidence is itself a `blocked` outcome, never silently reported as pass/fail without it (constitution §2).
- `passed-after-retry` (Req2 AC8) is a distinct enum value everywhere downstream (dashboard, Xray import, Jira), never collapsed into `passed` — enforced by using a 5-state enum (`passed`, `passed_after_retry`, `failed`, `ambiguous`, `blocked`) with a `blocked_reason` sub-field (`timeout` / `missing_precondition` / `setup` / `evidence_incomplete`), not booleans that could be left inconsistent. The precedence rule in §2.1 governs which value wins when more than one condition fires on the same step/run.
- **`blocked_reason: evidence_incomplete`** (resolves @qa's obs — the original 3 values had no bucket for this): covers the case where the capture tooling itself fails independent of preconditions/timeout/setup — e.g. the Evidence Writer can't reach the object store, a screenshot hook errors, or the video recording never starts. This is what makes the "a run missing required evidence is itself a blocked outcome" claim above actually testable against the enum.

### 2.5 Candidate Defect Grouper
- Triggers on `failed` and `blocked:setup` results only (`blocked:timeout` and `blocked:missing-precondition` are reported but not grouped into defects — they're test-infra/test-case issues, not candidate product bugs, matching Req2 AC3's "report separately from pass/fail" without implying every blocked run is a bug).
- **`ambiguous` does not reach the Grouper** (resolves @ux's obs on v7 + @qa's +1): §2.2's rule makes `ambiguous` strictly an authoring-gap signal (the step never specified a target at all — never a runtime regression). Filing a Jira bug for it would misroute a test-authoring problem into the product-defect pipeline, exactly what §2.2's rule exists to prevent. `ambiguous` joins `blocked:timeout`/`blocked:missing_precondition` in the same "reported, not grouped, not Jira-fileable" treatment Req2 AC3 already specifies — surfaced to the dashboard as a flat list (the "Run Health" list in ux-dashboard-spec.md), never as a candidate-defect card with an approve→file-Jira action. This takes option (a) from the blackboard discussion: removing `ambiguous` from the trigger list entirely, not just relabeling the Detail screen's action button — the button existing at all is the misroute risk, not just its label.
- Grouping key (Req3 AC1, "Decided"): `(xray_test_id, failing_step_id, root_cause_category)` where `root_cause_category ∈ {timing, network, environment, assertion, locator}`. This is a label the Result Processor assigns from the engine's raw error (e.g. element-not-found -> `locator`, connection reset -> `network`), not a raw stack trace match.
- New failures matching an existing open group or previously-filed Jira ticket attach to it (Req3 AC5) and expose the match basis (which key fields matched) in the dashboard so a reviewer can split a wrong auto-match (Req3 AC8).
- **Dismissed groups (resolves @ux's obs)**: a group the reviewer rejected (Req3 AC6) is marked `dismissed`, not deleted and not left matchable as if still open. A later failure with the same grouping key does **not** silently reattach to the dismissed group — the Grouper opens a *new* candidate, but links it to the prior dismissed group(s) with the same key and surfaces their dismissal reason in the detail view. This keeps the queue honest (a dismissed non-defect can't quietly keep resurfacing as if unseen, nor can it silently auto-suppress a recurrence that might now be real) while still giving the reviewer the prior context in one click — no auto-resolution either way, per constitution §3.
- **Post-split re-matching (resolves @ux's obs — flagged as a Grouper question, not a UI one)**: each group has its own `group_id`; splitting a failure out of a group (Req3 AC8) creates a new `group_id` that keeps the *same* grouping key as the original, since the key (test ID + step + root-cause category) is coarse enough that two genuinely distinct issues can legitimately share it — that's exactly why split exists. This means a key can map to more than one open group after a split. A later failure matching that key auto-attaches to the **most-recently-created** open group sharing it (a working default, not a guess dressed up as certainty), but the dashboard match-basis display (already required by Req3 AC8) explicitly shows "N open groups share this signature (last split <timestamp>)" whenever N>1, so the reviewer can re-split it again if the recency heuristic picked wrong. Same shape as the dismissed-group rule above: pick a non-blocking default, never hide that the default was a guess among options, per constitution §3.

### 2.6 Review Dashboard
- Two views per Req3 AC9: **queue** (grouped candidates, findings-first ordering per the Momentic/Mo market pattern — bugs surfaced to the top, not a raw run timeline) and **detail** (video deep-linked to the failure moment, screenshots, logs, match-basis/confidence shown as informational text, approve/reject/split actions).
- Confidence score on auto-matches is display-only — it never resolves a match or files a ticket by itself (constitution §3/§4; explicitly rejecting the Replay QA/bugAgent "auto-resolve by default" pattern).
- Every approve/reject records `{reviewer_identity, timestamp, decision, reason?}` (Req3 AC6-7). Reviewer identity comes from the auth/access-control layer (§2.7), not a free-text field.
- Setup/environment failures (Req4 AC6, `blocked:setup`) appear in the same queue under their own bucket, visually distinct from candidate defects — same surface, not a second tool.
- `ambiguous`, `blocked:timeout`, `blocked:missing_precondition`, and `blocked:evidence_incomplete` results (§2.5 — none of these reach the Grouper) surface in the same dashboard as a separate, non-actionable "Run Health" list: reported per Req2 AC3/AC6 and constitution §2 (a run with unusable evidence still needs to be visible to a human, even though it's not a candidate defect), but with no approve/reject/file-Jira action available, since none of these four are candidate defects.
- **Precondition-preset editing surface (resolves @ux's obs)**: the `operator` role (§2.7) edits `PreconditionPreset` objects through a form in the Review Dashboard (a dedicated "Presets" screen alongside the queue/detail views), not direct API/file edits. Keeping it in the same authenticated surface means preset edits inherit the same identity/access-control enforcement as approve/reject, rather than needing a second auth path.

### 2.7 Access Control / Identity
- The dashboard sits behind an identity provider (SSO/OIDC against whatever the org already runs — not a new user-store to build). Authenticated identity is what gets recorded on approve/reject (Req3 AC7) and determines who may approve defects or edit precondition presets (constitution §4).
- Scope of roles for v1: `reviewer` (approve/reject/split) and `operator` (edit precondition presets, trigger manual runs). A single person can hold both; this is an authorization boundary, not an org-chart decision.

### 2.8 Xray/Jira Client
- Talks to **Xray Cloud REST API** directly (Decided, requirements.md v1.2) for two things only: (a) importing execution results per run — linked to the Xray test case ID and build number, and (b) creating a Jira bug (via Xray's linkage) when a candidate defect is approved, with the grouped evidence URLs and Xray test ID(s) attached.
- Auth: `client_id`/`client_secret` API key pair (Jira Admin > Apps > Xray Settings > API Keys) tied to a dedicated service-account Jira user scoped to test-execution import + issue-create/attach only — not Jira admin. Exchanged for a 24h bearer token per call batch. Both the key pair and resulting tokens live in the secrets manager (Non-Functional Constraints); the client_secret itself needs a rotation policy since it doesn't auto-expire.
- **Jira Cloud confirmed** by the product owner (2026-10-24, requirements.md v1.3) — no Server/DC PAT-based variant needed. This component can be implemented as designed.

## 3. Shared configuration schema (Req4 + Req5)

One schema, not two mechanisms, per Req5 AC3:

```
RunConfig {
  xray_test_ids: [string]            // resolved from the "automation-stable" label if omitted
  device_platform: DevicePlatformTarget
  precondition_preset: string        // e.g. "new-player", "high-roller" — Req4 AC5
  precondition_overrides?: {         // per-test-case edits to the named preset, Req4 AC5
    [xray_test_id]: { [knob]: value }
  }
}

DevicePlatformTarget {
  platform: "mobile-ios" | "mobile-android" | "pc"   // v1 scope per product owner (2026-10-24):
                                                       // mobile + PC only, console explicitly excluded
  device_id_or_pool: string    // as CONFIGURED: a specific device id, or a pool name to resolve from
}

ResolvedDeviceTarget {         // resolves @qa's obs: what actually gets written to evidence/build metadata
  platform: string
  configured: string            // the pool name or device id as configured, verbatim
  resolved_device_id: string    // the ONE specific device the Execution Engine actually ran against,
                                 // even when `configured` was a pool — required for Req4 AC4 reproducibility
}

PreconditionPreset {
  name: string
  values: {
    account_level: ...
    currency: ...
    feature_flags: { [flag]: bool }
    server_time: timestamp | "now"
  }
  environment: "staging" | "non-prod-<name>"   // Req4 AC7 hard constraint: never "prod"
}
```

`environment` is validated against an allow-list at the Orchestrator before any precondition is applied — this is the enforcement point for Req4 AC7 (never shared/prod), not a convention left to whoever writes a preset.

The Result Processor (§2.4) writes `ResolvedDeviceTarget`, not the raw `DevicePlatformTarget`, into a run's evidence/build metadata (Req1 AC5, Req5 AC2) — so a pool-based run is reproducible per Req4 AC4 by the specific device it actually used, not just the pool name it was configured with.

## 4. Non-functional mapping (carried from requirements.md, unchanged)

| Concern | Decision | Owner component |
|---|---|---|
| Trigger | CI webhook primary, manual secondary | Run Orchestrator §2.1 |
| Evidence storage | External S3-compatible store, signed URLs, 90d default retention | Evidence Writer §2.3 |
| Credentials | Secrets manager, least-privilege service account | Xray/Jira Client §2.8 |
| Non-prod enforcement | Allow-listed `environment` field, validated before precondition apply | Config schema §3 |
| Access control | SSO/OIDC-backed identity, reviewer/operator roles | §2.7 |

## 5. Open items for implementation (not design blockers)

1. ~~Drizz self-heal signal~~ — superseded 2026-10-24: the engine choice changed (PixiJS/WebGL fact), see §2.2. **New open item**: confirm hands-on, against a real build, that (a) the game team can expose `globalThis.__PIXI_APP__` in QA/staging builds, (b) Playwright/Appium can reliably drive pointer/touch events against the real canvas end-to-end on PC and the mobile webview wrapper, and **(c) whether Drizz's vision-AI can reliably see/interact with this game's WebGL canvas in a mobile webview** — (c) is the task that actually resolves §2.2's still-open mobile (a)-Appium vs. (b)-Drizz choice; without it, that choice has no task tracking its Drizz-mobile half (resolves @qa's 2nd obs on design.md v6). Lower risk than the superseded spike (documented, reproducible pattern vs. an unconfirmed vendor claim), but still unverified against this game until someone runs it — and still blocked on real build/staging access (see blackboard, 2026-10-24).

~~2. Jira Cloud vs DC~~ — resolved 2026-10-24: product owner confirmed Jira Cloud (§2.8, requirements.md v1.3).
~~3. Game/platform scope~~ — resolved 2026-10-24: product owner confirmed mobile + PC for v1, console excluded (§3, requirements.md v1.3).

## 6. Traceability check against constitution.md

| Principle | Where enforced |
|---|---|
| §1 Honesty over automation claims | Result Processor's 5-state enum + precedence rule (§2.1, §2.4): `passed_after_retry` never aliased to `passed`, and self-heal (`ambiguous`) always outranks a plain retry pass |
| §2 Evidence-first reporting | Evidence Writer required before a result is considered complete; missing/failed capture is its own `blocked:evidence_incomplete` outcome, not a silent pass/fail (§2.3-2.4) |
| §3 Flag ambiguity, never guess | Orchestrator owns ambiguous/unresolved-precondition detection, not the execution engine (§2.1); the Playwright/Appium + PixiJS-scene-graph engine has no vendor self-healing to gate — an unresolvable target is structurally attributable to either `ambiguous` (no target specified — authoring gap) or `failed:locator` (target specified, missing at runtime — real regression), per the explicit rule in §2.2, never collapsed into one event or silently adapted |
| §4 Human review before filing | Dashboard approval is the only path to the Xray/Jira Client's Jira-create call (§2.6, §2.8) |
| §5 Full traceability | Every evidence object keyed by `{xray_test_id}/{build_number}/{run_id}` (§2.3); candidate defects link test ID + build + evidence (§2.5) |
| §6 Explicit, recorded preconditions | Shared config schema + allow-listed environment field (§3); applied values recorded with evidence (§2.3-2.4) |
