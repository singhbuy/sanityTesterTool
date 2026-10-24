# UX Spec: Review Dashboard

Status: **v1.2** — implements [design.md v9 §2.5-2.7](./design.md), governed by [constitution.md](./constitution.md). Covers build-order step 8 (dev's implementation plan, blackboard 2026-10-24T19:30:27Z).

**v1.2 changelog**: `ambiguous` removed from the candidate-defects bucket and moved to the Run Health list (§1) — design.md v8/v9 dropped `ambiguous` from the Grouper's trigger list entirely (resolving the S2.2/S2.5 contradiction this spec flagged) so it is never Jira-fileable, joining `blocked:timeout`/`blocked:missing_precondition`/`blocked:evidence_incomplete` as reported-but-not-grouped per Req2 AC3.

**v1.1 changelog**: added the post-split "N open groups share this signature" string to §2's match-basis display, per design.md v5's post-split re-matching rule (§2.5) resolving this spec's v1 open item.

Three screens behind one SSO/OIDC session (§2.7): **Queue**, **Detail**, **Presets**. No new auth path — all three inherit the same identity, used for `reviewer_identity` on approve/reject and for scoping who can touch Presets.

## 1. Queue

Default landing screen for the `reviewer` role.

**Grouping and ordering** (findings-first, per the Momentic/Mo pattern folded into design.md §2.6): candidate-defect groups (from `failed`/`blocked:setup`, §2.5) sorted newest-activity-first within two buckets, buckets never interleaved:

| Bucket | Contents | Row label shown |
|---|---|---|
| **Candidate defects** | Open groups from `failed` | `root_cause_category` + failing step name (e.g. "Timing — Lobby load step"), not a raw stack trace — per @qa's grouping-label recommendation |
| **Blocked: setup** | `blocked:setup` groups | Same label shape, prefixed "Setup — " so it reads as infra, not product bug, per Req2 AC3 |

`ambiguous`, `blocked:timeout`, `blocked:missing_precondition`, and `blocked:evidence_incomplete` are **not** in this queue and never show an approve/file-Jira action anywhere — design.md v8/v9 §2.5 excludes all four from the Grouper's trigger list (`ambiguous` specifically because it's a test-authoring gap, never a candidate defect, per §2.2's `ambiguous`-vs-`failed:locator` rule — a dashboard button would be a standing invitation to misroute it regardless of its label). All four surface in a separate read-only "Run Health" list on the same screen (not a second tool, per §2.6), sorted by recency, no actions — just test ID, build, reason, link to raw evidence. A reviewer still needs to *see* each of these (constitution §1 — absence of a clean pass is itself reportable), just never act on them from here.

**Each queue row shows:**
- Grouping label (category + step)
- Occurrence count (how many failures are attached to this group)
- Match-basis badge if this group absorbed a newer failure via auto-match (Req3 AC5) — e.g. "auto-matched (test_id + step + category)" — informational only, never a reason the row is hidden or pre-resolved
- **Recurrence badge** if this group was opened because a prior group with the same key was dismissed (§2.5) — e.g. "⚠ recurs after dismissal" — this is the one case where a queue row needs a visual flag beyond the category label, since it's the scenario most likely to get reviewer-fatigue-skipped
- Last-seen build number and timestamp

**Empty state:** "No candidate defects — N runs clean since [last dashboard visit or 24h, whichever is shorter]." Never a bare blank screen; absence of findings is itself a reportable fact per constitution §1.

**Row click** → Detail.

## 2. Detail

One candidate-defect group (or one setup-blocked group) per screen.

**Layout, top to bottom:**
1. **Header**: grouping label, occurrence count, Xray test ID(s), build number(s), `root_cause_category`.
2. **If recurrence-flagged**: a collapsed-by-default "Prior dismissal" panel — who dismissed the earlier group, when, and their reason (§2.5's "surfaces their dismissal reason in the detail view"). Collapsed so it doesn't dominate the screen, but one click away — the design intent is "give context, don't pre-judge."
3. **Evidence, most recent occurrence first**: video player deep-linked to the failure moment (not full-run scrub — the Momentic/Mo pattern this was built to borrow), screenshots at the failing step, log excerpt. A visible control to step back through older occurrences in the same group without leaving the screen.
4. **Match basis** (if auto-matched): which key fields matched (`test_id` / `step` / `category`), shown as plain text next to the evidence, not a score bar or anything implying statistical confidence — design.md §2.6 is explicit this is informational, never auto-resolving. When a grouping key spans more than one open group after a split (design.md v5 §2.5), the same plain-text area shows `"N open groups share this signature (last split <timestamp>)"` whenever N>1, so the reviewer can see the recency-based auto-attach was a default among options and re-split again if it picked wrong — same treatment as the dismissed-group recurrence badge in §1, not a new UI pattern.
5. **Actions**: `Approve → file Jira bug`, `Reject / dismiss`, `Split out`. All three require confirmation (no single-click destructive/terminal action); `Reject` and `Split` require a reason field (`decision.reason`, §2.6); `Approve` doesn't require one but allows an optional note.

**Post-action feedback:** the row disappears from the queue immediately with a toast naming the action taken and by whom (self-confirmation, not just a silent row removal) — reviewers doing triage in a batch need to trust the queue updated, not wonder if the click registered.

**Split out:** spawns a new group from the selected occurrence(s), inherits the same detail-screen shape; original group's occurrence count decrements. This is the one action that doesn't close the current screen — it should keep the reviewer on the (now-smaller) original group to keep working through remaining occurrences.

## 3. Presets

Separate screen, `operator` role only (§2.7) — `reviewer`-only accounts don't see this nav item at all, not just a disabled button, since Presets isn't relevant to their triage work.

**List view:** named presets (`new-player`, `high-roller`, ...) with `environment` shown per preset. Any preset whose `environment` would resolve outside the allow-list is blocked at save time with an inline error naming the allowed values — the UI never lets an operator type a free-text environment string that the Orchestrator would reject later (Req4 AC7 enforcement happens here too, not only server-side, so the operator isn't told "invalid" after the fact).

**Edit form:** one form per preset — `account_level`, `currency`, `feature_flags` (toggle list, not raw JSON), `server_time` (either a fixed timestamp or "now", exposed as a literal choice, not a text field someone has to know the magic string for). Per-test-case `precondition_overrides` (Req4 AC5) are edited from the same form via an "Override for specific test case" sub-section, not a separate screen — keeps the one-schema intent from design.md §3 visible in the UI, not just in the data model.

**Save** records `{editor_identity, timestamp}` alongside the preset, same pattern as approve/reject, since preset edits are also an accountable action (§2.7).

## 4. Cross-cutting

- **Header on all three screens**: authenticated identity + role(s), consistent with §2.7's "a single person can hold both" — if someone has both roles, both nav items (Queue/Detail, Presets) are visible, no mode switch required.
- **No screen silently retries or auto-dismisses.** Every state change a human can see traces back to either an explicit human action (approve/reject/split/preset-save) or an upstream system fact (new occurrence, new build) — never a background job quietly resolving something while the reviewer isn't looking, per constitution §3/§4.
- **Loading/error states**: if evidence (video/screenshot/log) fails to load from the signed URL (expired, store unreachable), the Detail screen shows that failure explicitly next to where the evidence would be — never a blank player or a silently-missing screenshot that looks like "there was no evidence" when the real story is "the evidence failed to load."

## 5. Open items / handoff notes

- Exact visual design (layout grid, component library, color system) is implementation's call — this spec fixes information architecture and interaction rules, not pixels.
- ~~Split-out's downstream grouping behavior~~ — resolved in design.md v5 §2.5 (2026-10-24): post-split matches attach to the most-recently-created open group sharing the key, surfaced via the "N open groups share this signature" string now in §2 above.
- Depends on build-order steps 6 (Grouper) + 7 (Access Control) per dev's plan (2026-10-24T19:30:27Z) before this can be wired to real data; this spec itself has no such dependency and can be reviewed/refined now.
