### 2026-10-24T18:53:28Z ux claim
Taking UX review of specs/requirements.md (Draft, pending approval before design.md) — focusing on the human-review workflow for candidate defects (Req 3) and the precondition config UX (Req 4).

### 2026-10-24T18:57:53Z ux reply
re 2026-10-24T18:53:40Z qa ask (device/platform): agree with @dev's split — separate AC for device/platform selection, not folded into Req4. UX note: both that AC and Req4's precondition knobs are 'pre-run configuration' from an operator's point of view, so even as separate ACs they should share one config surface/schema in design.md rather than two unrelated config mechanisms.

### 2026-10-24T18:57:53Z ux obs
UX review of Req3 (human-review workflow): no AC defines the REJECT/dismiss path. AC4 only covers approve→Jira. Need an explicit AC for 'human rejects candidate defect' — is it dismissed, marked reviewed-not-a-defect, and does that feedback improve future grouping (AC1/AC5)? Without it, the review UI has only one button.

### 2026-10-24T18:57:53Z ux obs
UX review of Req3: no AC records reviewer identity/accountability for the approve action (constitution #4 'human review before filing' implies someone is accountable). Recommend adding: approved candidate defects record who approved and when, alongside the Jira link — needed for audit, not just the ticket itself.

### 2026-10-24T18:57:53Z ux obs
UX review of Req3 AC5 (auto-match new failure to existing candidate/ticket): no AC exposes match confidence or lets a reviewer override a wrong auto-match. Mis-attached evidence breaks traceability (constitution #5). Recommend the review UI show why a failure was matched and allow 'split out' as an explicit action.

### 2026-10-24T18:57:53Z ux obs
UX recommendation for open question 'who reviews, where': a dashboard, not Slack/email. Constitution #2 requires evidence-first reporting (screenshots, full video, logs, build metadata) — email/chat threads can't host a video player + log viewer + screenshot gallery per candidate defect well. Propose a queue view (grouped candidates) + detail view (evidence + approve/reject/split actions) as the review surface for design.md.

### 2026-10-24T18:57:53Z ux obs
UX review of Req4 (precondition config): AC1-4 only cover recording the APPLIED value and reproducing it later — no AC defines how a human/operator specifies the DESIRED precondition values before a run (per-run form, per-test-case config file, named presets?). That input-side UX is currently undefined and needed before design.md.

### 2026-10-24T18:57:53Z ux obs
UX review of Req4 AC3 (setup/precondition failure stops run, reported as setup/environment issue): no AC says where that failure surfaces. Recommend it land in the same review surface as Req3's candidate defects (distinct 'blocked: setup' bucket, not pass/fail) so operators have one place to look, consistent with Req2 AC3's 'blocked: missing precondition' reporting.

### 2026-10-24T18:57:53Z ux done
UX review of Req3 (human-review workflow) and Req4 (precondition UX) complete — 6 obs + 1 reply logged above. Summary for @dev's design.md: (1) need an explicit reject/dismiss AC for Req3, (2) record reviewer identity on approval, (3) expose+allow override of auto-match confidence (AC5), (4) single dashboard (queue+detail, not Slack/email) as the review surface, (5) Req4 needs an AC for how desired precondition values are specified, not just recorded, (6) setup/precondition failures should surface in the same review surface as candidate defects. No blockers on my end for design.md to start, provided these become explicit ACs or logged open decisions.

### 2026-10-24T19:02:27Z ux reply
re 2026-10-24T19:01:24Z devops obs: agreed — real auth/identity layer on the dashboard covers my 'record reviewer identity' ask for free instead of a free-text name field. No objection, fold into design.md's infra section.

### 2026-10-24T19:02:27Z ux claim
Taking @pm's research ask: how autonomous bug-report agents (Momentic/Mo, Replay QA, bugAgent) present evidence-backed reports to a human reviewer — looking for patterns to borrow/avoid for the Req3 dashboard (queue+detail, approve/reject/split).

### 2026-10-24T19:03:06Z ux obs
Market research (Momentic/Mo): borrow this pattern for Req3 dashboard — findings-first queue (sorted, bugs surfaced to top, not a raw trace/timeline first), and a deep-link per finding that jumps the video straight to the failure moment instead of making the reviewer scrub a full run video. Each bug report bundles repro steps + logs + screenshots + video replay as one shareable unit — this maps almost directly onto our Req1 evidence set (screenshot/video/logs/build metadata), good validation our evidence bundle shape is right.

### 2026-10-24T19:03:06Z ux obs
Market research (bugAgent): borrow surfacing a numeric confidence/classification score per item — directly useful for our AC8 (auto-match exposes its basis). AVOID their 'zero manual triage' auto-classification-as-default framing: that's the opposite of constitution #3/#4. In our dashboard, confidence is informational only, never a substitute for the human approve/reject/split action.

### 2026-10-24T19:03:06Z ux obs
Market research (Replay QA): its default flow pipes root-caused bug reports straight to an auto-fix 'software factory' with no mandatory human gate before action is taken — this is the anti-pattern to explicitly avoid. Our Req3 AC6/AC7/AC9 (reject path, reviewer identity, dashboard review) must stay a hard, non-skippable gate before any Jira issue is filed, not an optional review step bolted on after automated action.

### 2026-10-24T19:03:06Z ux done
Completed @pm's research ask: surveyed Momentic/Mo, Replay QA, bugAgent for how they present evidence-backed reports to a human reviewer. 3 obs logged above. Net for design.md's Req3 dashboard: (1) findings-first queue + jump-to-moment video deep links, (2) show auto-match confidence score per candidate (informational, not auto-resolving), (3) keep our mandatory human-approval gate explicit and non-skippable — most of these market tools default to weaker or skippable review gates, which conflicts with constitution #3/#4 and should NOT be copied. No blockers; nothing here changes requirements.md v1.1, this just confirms the Req3 AC6-AC9 shape is on the right track.

### 2026-10-24T19:07:57Z ux reply
re 2026-10-24T19:04:51Z pm warn: ack, recreated my cron job pointing at /Users/yogendrabundela/Documents/GitHub/AI/SanityTesterTool/blackboard/bb (old one deleted). Using that path from here on.

### 2026-10-24T19:07:57Z ux obs
re @qa's reusable grouping idea (root-cause-category + step, not raw stack trace, for Req3 AC1): if adopted, the dashboard queue (my AC9 recommendation) should show that category as the grouping label a reviewer sees per candidate — e.g. 'Timing — Lobby load step' — not a raw stack trace, so the queue stays scannable. Flagging for whoever writes the dashboard section of design.md.

### 2026-10-24T19:15:35Z ux obs
design.md review (§2.7, §3): the 'operator' role can 'edit precondition presets' but no UX surface is specified for it — is preset authoring a form in the Review Dashboard, a separate admin screen, or direct edits to the PreconditionPreset config object (API/file)? Req4 AC5 is satisfied data-model-wise (named presets + per-test-case overrides) but the actual editing surface is still undefined, same gap I flagged pre-design, just moved one layer down.

### 2026-10-24T19:15:35Z ux obs
design.md review (§2.5-2.6): reject/dismiss (Req3 AC6) records reviewer_identity+timestamp+decision+reason, but nothing says whether a rejected candidate is excluded from future auto-matching (Req3 AC5/AC8). Without that, a dismissed non-defect can keep resurfacing to reviewers every subsequent run with the same signature — recommend the Grouper check reject status on existing groups before reattaching a new failure, otherwise the queue's 'findings-first' trust (my earlier market-research recommendation) erodes fast.

### 2026-10-24T19:15:35Z ux done
Reviewed design.md v1 against my requirements.md obs for @dev: all 6 original asks + all 3 market-research patterns are incorporated (reject path w/ identity §2.6, confidence as informational-only+override §2.5-2.6, dashboard queue+detail as sole review surface §2.6, blocked:setup in same queue §2.6, findings-first ordering + jump-to-moment video + root-cause-category grouping label all present). 2 new obs logged above: (1) precondition-preset editing UX surface still unspecified, (2) rejected candidates' effect on future auto-matching unspecified. Neither is a blocker — both are refinements for whoever builds §2.6/§2.7 and §2.5's matching logic respectively.

### 2026-10-24T19:20:45Z ux obs
re @qa's 2026-10-24T19:18:35Z obs (passed_after_retry vs forced-ambiguous precedence): this isn't just an enum-semantics gap, it decides whether a self-healed step ever reaches the Review Dashboard at all. §2.5's Grouper only triggers on failed/ambiguous/blocked:setup — if the precedence rule resolves a self-healed retry to passed_after_retry instead of ambiguous, that run never enters the queue, which directly contradicts my original design.md ask (§2.2's 'every self-heal event MUST map to ambiguous') and constitution §3. Recommend the precedence rule be hard-coded: ambiguous (AC9) always wins over passed_after_retry (AC8) when both conditions fire on the same step — never the reverse.

### 2026-10-24T19:25:41Z ux done
Reviewed design.md v2 directly (not just pm's decision replies). Confirmed both my obs resolved correctly: (1) §2.6 preset editing is a dedicated 'Presets' form in the Review Dashboard, inheriting the same SSO/OIDC auth as approve/reject — matches my ask; (2) §2.5 dismissed groups are marked dismissed (not deleted/left matchable) and a recurrence opens a fresh candidate linked to the prior dismissal with reason shown in detail view — correctly avoids both silent resurfacing and silent auto-suppression, per constitution §3. Also confirmed the ambiguous>passed_after_retry precedence (§2.1/§2.4) landed exactly as pm decided. Sign-off from UX: design.md v2 is good as written, no blockers, nothing further from me pending only the 2 non-blocking open items (Jira Cloud/DC, game/platform scope) PM is chasing.

### 2026-10-24T19:35:36Z ux claim
Taking @dev's ask: dashboard visual/interaction design for build-order step 8 (Review Dashboard, design.md S2.6) — queue, detail, and presets screens, independent of steps 1-7. Will post the interaction spec (screen layouts, states, actions, empty/error states) as an obs + a new specs/ux-dashboard-spec.md, not a design.md rewrite.

### 2026-10-24T19:36:28Z ux done
Dashboard UX spec drafted: specs/ux-dashboard-spec.md v1, implements design.md v4 S2.6-2.7. Covers 3 screens: (1) Queue — findings-first, candidate-defects vs blocked:setup as separate buckets, blocked:timeout/missing_precondition/evidence_incomplete in a separate read-only 'Run Health' list (not grouped per S2.5), recurrence badge for groups reopened after a dismissal; (2) Detail — video deep-linked to failure moment, collapsed prior-dismissal panel, match-basis as plain text (never a score bar), approve/reject/split all require confirmation, reject/split require a reason, split keeps reviewer on the shrunk original group; (3) Presets — operator-only screen, environment allow-list enforced client-side at save (not just server-side), feature-flags as toggles not raw JSON, per-test-case overrides in the same form (one schema, one screen, matching design.md S3's intent). Also specified cross-cutting rules: no screen silently auto-resolves anything, evidence-load failures shown explicitly (never a blank player that reads as 'no evidence'). One open item flagged for whoever builds S2.5+S2.6 together: split-out's downstream re-matching behavior isn't fully specified, it's a Grouper question more than a UI one. No dependency on build-order steps 1-7 — ready for review now.

### 2026-10-24T19:46:04Z ux reply
re 2026-10-24T19:40:37Z dev done (split-out re-matching, design.md v5 S2.5): added the exact 'N open groups share this signature (last split <timestamp>)' string to ux-dashboard-spec.md v1.1 S2's match-basis display, same treatment as the existing dismissed-group recurrence badge — no new screen/pattern needed, confirmed. Marked my spec's old open item resolved.

### 2026-10-24T19:56:14Z ux obs
design.md v7 review (@pm's 'flag anything off' ask): S2.2's new rule states 'only [failed:locator] is a candidate defect' and explicitly warns that collapsing ambiguous+failed 'would misroute authoring defects into the defect-filing pipeline' -- i.e. ambiguous (authoring gap: step never specified a target) is NOT supposed to be a candidate defect. But S2.5 (Grouper) was not touched in the v7 changelog and still says 'Triggers on failed, ambiguous, and blocked:setup' -- grouping ambiguous alongside failed as if both feed the same Review Dashboard queue with the same approve->file-Jira-bug action. As written, S2.2 and S2.5 contradict each other on whether ambiguous results reach the defect-filing pipeline at all. This matters for my dashboard spec (ux-dashboard-spec.md's Queue/Detail 'Approve -> file Jira bug' action) -- if ambiguous stays in the Grouper's trigger list unchanged, a reviewer could file a Jira product-bug for what S2.2 just defined as a test-authoring problem, exactly the misrouting S2.2 warns against. Recommend S2.5 either (a) drop ambiguous from the Grouper trigger list and route it to a separate 'test authoring issues' bucket (parallel to blocked:timeout/missing_precondition -- reported, not grouped into defects, not Jira-fileable), or (b) if ambiguous results should still reach a human via the dashboard, make the Detail screen's action for an ambiguous item explicitly NOT 'file Jira bug' (e.g. 'flag test case for authoring fix' instead) so the UI doesn't offer the misroute S2.2 is trying to prevent. Flagging to @dev/@pm since this is a S2.5 edit, not a UI-only fix -- I'll hold my dashboard spec's Approve-action wording until this is resolved.

### 2026-10-24T20:00:41Z ux reply
re 2026-10-24T19:58:15Z qa reply: agreed, (a) is the right fix and the Req2 AC3 anchor settles it -- a dashboard button is a standing invitation regardless of its label, so removing ambiguous from S2.5's Grouper trigger list is the only way to actually prevent the misroute, not just discourage it. Once @dev updates S2.5, I'll move ambiguous into ux-dashboard-spec.md's existing read-only 'Run Health' list (§1, same bucket already holding blocked:timeout/missing_precondition/evidence_incomplete) alongside its screenshot/log/video evidence link, no actions -- consistent with how that list already treats non-defect-eligible outcomes. Holding that edit until S2.5 actually changes, same as I said before.

### 2026-10-24T20:06:00Z ux done
Unblocked edit applied: ux-dashboard-spec.md v1.2. Removed ambiguous from the Queue's candidate-defects bucket (S1) -- it never shows an approve/file-Jira action anywhere now. ambiguous joins blocked:timeout/blocked:missing_precondition/blocked:evidence_incomplete in the read-only Run Health list, matching design.md v9 S2.5/S2.6/S1 diagram exactly. Candidate-defects bucket is now failed-only (blocked:setup keeps its own separate bucket, unchanged). S2.2/S2.5 contradiction fully closed end-to-end across both spec files.

### 2026-10-24T22:25:52Z ux reply
Ack new git-workflow policy (PROTOCOL.md S5 / .claude/skills/git-workflow). Read the skill directly (not yet in my loaded skill list this session). Going forward: commit locally after any blackboard entry or spec edit of mine, never push -- same as everyone else. ux-dashboard-spec.md v1.2 was already captured in the initial commit, nothing of mine pending beyond this ack.

