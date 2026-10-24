# Requirements: Xray/Jira Game Sanity Test Automation

Status: **Approved for design — v1.4** (PM sign-off; execution-engine decision revised after PixiJS/WebGL fact — supersedes v1.3)

Governed by [constitution.md](./constitution.md).

## Requirement 1: Automated Sanity Test Execution with Evidence Capture

**User Story:** When running repetitive sanity tests on a new game build, I want to automatically execute a stable subset of Xray/Jira test cases with screenshots, video, logs, and build metadata, so I can save QA time while still producing evidence engineers can actually triage.

### Acceptance Criteria
1. WHEN a new game build is available THEN the system SHALL execute the configured stable subset of Xray test cases against that build without manual step-by-step operation.
2. WHILE executing a test case THEN the system SHALL capture a screenshot at each defined verification step.
3. WHEN a test case run completes (pass or fail) THEN the system SHALL attach a full-run video recording.
4. WHEN a test case run completes THEN the system SHALL capture and persist device/OS-level and app-level client logs covering the run's duration. Server-side logs are out of scope for v1 unless trivially available from the CI pipeline.
5. WHEN a test case run completes THEN the system SHALL record build metadata (build number, environment, timestamp) alongside the result, including the device/platform target selected per Requirement 5.
6. IF the configured stable test subset changes THEN the system SHALL support re-selection via configuration, with no code changes required.

## Requirement 2: Ambiguity and Precondition Detection

**User Story:** When Xray test cases are vague or missing setup details, I want the tool to flag ambiguous steps and unresolved preconditions instead of guessing, so I can distinguish bad test-case authoring from real product defects.

### Acceptance Criteria
1. WHEN a test step lacks a machine-resolvable action or expected result THEN the system SHALL mark the step `ambiguous` rather than inferring intent.
2. WHEN a required precondition is not explicitly defined in the test case THEN the system SHALL mark it `unresolved` rather than assuming a default value.
3. WHEN a run contains ambiguous steps or unresolved preconditions THEN the system SHALL report these separately from pass/fail outcomes.
4. IF a run cannot proceed because of an unresolved precondition THEN the system SHALL stop and report `blocked: missing precondition` rather than reporting a test failure.
5. WHEN the system flags an ambiguity or unresolved precondition THEN the system SHALL NOT report the run's outcome as a full automated success.
6. IF a step or run exceeds its configured timeout THEN the system SHALL stop and report `blocked: timeout`, distinct from an assertion failure, an `ambiguous` step, or an `unresolved precondition`.
7. WHEN a step fails transiently THEN the system SHALL retry it at most N times (configurable, default 1) before marking it a failure; each retry attempt and its outcome SHALL be recorded as evidence.
8. IF a run passes only after one or more retries THEN the system SHALL mark the result "passed after retry" — never reported identically to a clean first-attempt pass (constitution §1).
9. IF the underlying execution engine itself performs automatic adaptation or self-healing (e.g. re-resolving a changed locator, interpreting a vague step) THEN that adaptation SHALL be surfaced as an `ambiguous`/flagged event — never a silent pass, regardless of vendor. (No surveyed market tool does this by default — see blackboard research 2026-10-24; this must hold even when the execution engine is a third-party product.)

## Requirement 3: Reviewed, Traceable Defect Reporting

**User Story:** When automated UI runs fail or produce potential bugs, I want failures grouped, linked to existing Xray IDs, and reviewed before Jira bugs are created, so I can avoid duplicate tickets and keep test history connected to the source cases.

### Acceptance Criteria
1. WHEN multiple test case runs fail with a similar signature THEN the system SHALL group them into a single candidate defect. "Similar signature" = same Xray test case ID + same failing step + same root-cause category (timing / network / environment / assertion / locator) — not raw stack-trace matching.
2. WHEN a candidate defect is created THEN the system SHALL link it to the originating Xray test case ID(s), build number, and evidence (video/logs).
3. WHEN a candidate defect exists THEN the system SHALL hold it for human review before any Jira issue is filed.
4. WHEN a human approves a candidate defect THEN the system SHALL create the Jira bug with the grouped evidence and Xray linkage attached.
5. IF a new failure matches an already-open candidate or previously filed defect THEN the system SHALL attach it to the existing group/ticket instead of creating a duplicate.
6. WHEN a human rejects a candidate defect THEN the system SHALL mark it `dismissed` (not a defect) rather than leaving it pending, and SHALL retain the rejection reason.
7. WHEN a human approves or rejects a candidate defect THEN the system SHALL record the reviewer's identity and timestamp alongside the decision.
8. WHEN the system auto-attaches a new failure to an existing candidate/ticket (AC5) THEN it SHALL expose the match basis to the reviewer and allow the reviewer to split the failure into a separate candidate.
9. The candidate-defect review surface SHALL be a dashboard providing a queue view (grouped candidates) and a detail view (evidence + approve/reject/split actions) — not an email- or chat-based workflow.

## Requirement 4: Explicit Precondition Configuration and Recording

**User Story:** When shared test accounts or game states are unreliable, I want known preconditions like account level, currency, feature flags, and server time to be explicitly configured and recorded, so I can reproduce test results and avoid wasting time on environment or account-state issues.

### Acceptance Criteria
1. WHEN a test run requires a known precondition (account level, currency, feature flags, server time) THEN the system SHALL set that precondition explicitly rather than relying on ambient/shared state.
2. WHEN a precondition is set THEN the system SHALL record the exact value applied alongside the run's evidence.
3. IF setting a precondition fails THEN the system SHALL stop and report the failure as a setup/environment issue, not a test failure.
4. WHEN a run is reproduced later THEN the recorded precondition values SHALL be sufficient to recreate the same starting state.
5. WHEN configuring a run THEN desired precondition values SHALL be specifiable via named presets (e.g. "new-player", "high-roller") that are editable per test case, rather than only recorded after the fact.
6. WHEN a precondition cannot be set (AC3) THEN the resulting setup/environment failure SHALL surface in the same review dashboard as Requirement 3's candidate defects, in a distinct `blocked: setup` bucket.
7. Requirement 4's server-time and feature-flag manipulation SHALL only run against a dedicated non-production/staging environment with its own test accounts — never a shared or production account/environment.

## Requirement 5: Device/Platform Target Selection

**User Story:** As a QA engineer configuring a run, I want to explicitly select the device/platform target, so the automation surface is unambiguous and the result is reproducible.

### Acceptance Criteria
1. WHEN a run is triggered THEN the system SHALL execute against an explicitly selected device/platform target rather than an implicit default.
2. WHEN a run executes THEN the selected device/platform target SHALL be recorded alongside the build metadata (Requirement 1, AC5).
3. Device/platform selection and Requirement 4's precondition values SHALL be configured through one shared configuration surface/schema, not two unrelated mechanisms.

## Non-Functional / Infra Constraints

- **Trigger**: a CI pipeline webhook (post-build step) is the run trigger for v1; manual trigger is a supported secondary path. CI is the authoritative source for build number/environment/timestamp.
- **Evidence storage**: screenshots, video, and logs are stored in an external, S3-compatible object store, with signed links attached to the Jira/Xray issue — not Jira attachments directly. Default retention: 90 days, configurable.
- **Credentials**: Xray/Jira API credentials live in a secrets manager (e.g. Vault/SSM), never in env vars or repo config. The service account is scoped to issue-create + attach only — not full Jira admin.
- **Environment**: Requirement 4's server-time and feature-flag manipulation requires a dedicated non-production/staging environment with its own test accounts (Requirement 4, AC7).
- **Access control**: the Requirement 3 review dashboard (AC9) requires a real identity/access-control layer (authenticated users, not a free-text name field) — this is also what satisfies AC7's "record the reviewer's identity" requirement in practice, and governs who may approve candidate defects or set preconditions (constitution §4).

## Decided (resolved via blackboard research, 2026-10-24)

- **Stable subset definition**: Xray-tagged (a curated label/folder, e.g. `automation-stable`), human-curated — not inferred from pass-rate history for v1.
- ~~Execution engine / device target for Requirement 5: prototype Drizz first, Airtest+Poco fallback, AltTester+Appium as device-farm path~~ — **SUPERSEDED 2026-10-24** (see below). That research assumed a native-engine game (Unity/Unreal/Godot); the actual game renders via **PixiJS/WebGL**, which invalidates most of it.
- **Execution engine / device target for Requirement 5 (revised, 2026-10-24)**: the game renders via **PixiJS/WebGL**, in a browser (PC) or mobile webview — not a native Unity/Unreal/Godot binary. Re-check against the real stack: **Airtest+Poco** has no WebGL/PixiJS driver at all (its drivers are Android/iOS-native, Windows, Unity3D, cocos2d-x only) — not viable as a fallback, full stop. **AltTester+Appium** is Unity-SDK-only — not viable. **Maestro** remains ruled out (no accessibility tree for a rendered canvas). **Drizz** is additionally disqualified for this scope specifically: it's a mobile-only platform (iOS/Android/mobile-web) with no desktop-browser support, so it cannot cover Req5's PC half of v1 scope regardless of the canvas question, and its own marketing is internally inconsistent about whether its "mobile web" support even reaches WebGL canvas content.
  - **New primary**: **Playwright** (PC, native browser) + **Appium WebView-context switching** (mobile webview) — both driving the same technique: read the live PixiJS scene graph via the engine's own official devtools exposure hook (`@pixi/devtools` / `globalThis.__PIXI_APP__` — a one-line hook, not a heavyweight SDK embed), resolve the target object's `boundingBox()` at runtime, convert to canvas-relative coordinates, and dispatch a real pointer/touch event — the direct equivalent of Poco's object-level introspection, but for this game's actual stack. Confirmed as an established pattern by non-vendor sources: an ASE 2022 academic paper and its published PixiJS visual-testing framework (`asgaardlab/canvas-visual-bugs-testbed`), and PixiJS's own first-party devtools package — not vendor marketing claims.
  - **Structurally resolves Req2 AC9 for this engine**: there is no vendor self-healing black box to gate — object resolution is an exact scene-graph lookup, so a missing/moved object is a clean, attributable "locator not found" failure, never a silent AI-guessed adaptation. The previously-planned Drizz self-heal-signal spike is no longer needed.
  - **Evidence capture (Req1 AC2-3)**: Playwright's built-in screenshot/video/trace recording covers this with no extra harness work; Appium/device-farm log capture covers AC4 on mobile.
  - **PC has no viable off-the-shelf engine at all** (confirmed independently by @qa's parallel research) — Playwright + the scene-graph hook is mandatory for PC regardless of how any mobile-engine spike goes, not an optional fallback.
  - **Mobile keeps two live candidates, not a single choice yet**: (a) Appium WebView-context + the same scene-graph hook (consistent technique with PC, no vendor dependency), or (b) **Drizz**, narrowed from "primary for everything" to "possible mobile-only candidate" — its vision-AI reads rendered pixels, so it may not care about WebKit/mobile-Safari DOM quirks the way a webview-context approach does, which is relevant to @devops's mobile-Safari real-device-cloud cost concern. Still gated on its own self-heal-signal verification (narrower in scope now: mobile-only, not whole-system) and still unconfirmed hands-on. Pick between (a)/(b) after the Step-0 spike below runs on both.
  - **Remaining spike before implementation** (replaces the old Drizz self-heal spike): confirm hands-on, against a real build, that (a) the game team can expose `globalThis.__PIXI_APP__` (or equivalent) in QA/staging builds, and (b) Playwright/Appium can reliably drive pointer/touch events against the real canvas end-to-end on both PC and the mobile webview wrapper. Lower risk than the superseded spike (based on a documented, reproducible pattern rather than an unconfirmed vendor claim), but still unverified against *this* game until someone runs it.
- **Req3 AC1/AC5 "similar signature"**: now written into AC1 above as test ID + failing step + root-cause category (timing/network/environment/assertion/locator).
- **Xray/Jira integration mechanism**: direct **Xray Cloud REST API** (not Jira REST + Xray fields, not a CI plugin) — used to both import execution results and attach evidence. Auth: a dedicated Jira service account scoped to test-execution/issue-create+attach only, with a client_id/client_secret API key pair generated under Jira Admin > Apps > Xray Settings > API Keys. That pair is exchanged for a bearer token (24h expiry) per call batch; the client_secret itself does not auto-expire, so it needs its own rotation policy in the secrets manager (same store as the other Xray/Jira creds — see Non-Functional/Infra Constraints). This decision targets **Jira Cloud**, confirmed by the product owner (2026-10-24) — see the Jira edition confirmation bullet below.
- **Xray-Functionize self-healing risk**: moot for v1 — the chosen execution engines (Drizz prototype, Airtest+Poco fallback, see above) don't go through Functionize at all, so its heal-flag/API-visibility gap doesn't block us. Req2 AC9's rule (any engine's self-healing/adaptation must surface as a flagged event, never a silent pass) stands as the general safeguard regardless of which engine design.md ultimately picks.
- **Market scan for "ambiguous/flaky vs. real failure" (constitution #3)**: confirmed nothing in the surveyed market (Xray-Functionize, Momentic, general flaky-detection tooling) defaults to flag-and-stop — they self-heal, auto-filter, or auto-label via retry-pass instead, with at best a post-hoc manual-triage bucket (Momentic's Quarantine). Req2 AC1/AC2 must be built as specified, not bought.
- **Req3 dashboard UX**: informed by market scan of Momentic/Mo, Replay QA, bugAgent — adopt findings-first queue ordering, deep-link-to-failure-moment on run video, and a per-candidate confidence/match-basis score shown as informational only (never auto-resolving, per constitution #3/#4). Explicitly reject these tools' weaker/skippable review gates — Req3 AC6/AC7/AC9's human approval stays a hard, non-skippable gate.
- **Platform scope for v1** (product owner decision, 2026-10-24): **mobile and PC only**. Console is explicitly out of scope for v1 — no console device-farm/dev-kit tooling decision is needed, and `DevicePlatformTarget.platform` (design.md §3) is narrowed to `mobile-ios | mobile-android | pc`.
- **Jira edition confirmation** (product owner, 2026-10-24): confirmed **Jira Cloud**. The Xray/Jira integration-mechanism decision above (direct Xray Cloud REST API, client_id/secret + bearer token) stands as designed — no Server/DC PAT-based variant needed.

## Open Questions (remaining)

None outstanding. Both prior open questions (platform scope, Jira edition) are resolved above.
