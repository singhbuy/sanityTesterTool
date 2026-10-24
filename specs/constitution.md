# Project Constitution

These principles govern every requirement, design decision, and task for this project. Any spec or implementation that conflicts with a principle here must change the principle explicitly (with reasoning recorded) rather than quietly violate it.

## 1. Honesty over automation claims
The tool must never report a run as a clean automated pass if any part of it was ambiguous, blocked, or required an assumption. Partial or uncertain results are reported as such — not rounded up to "success."

## 2. Evidence-first reporting
No result is reported without the evidence that backs it: screenshots at verification steps, a full run video, logs for the run's duration, and build metadata (build number, environment, timestamp). A result without evidence is not a usable result.

## 3. Flag ambiguity, never guess
When a test case's steps or preconditions are vague, incomplete, or missing, the system flags this explicitly (`ambiguous` / `unresolved precondition`) instead of inferring intent. This preserves the distinction between "the test case was badly authored" and "the product has a real defect."

## 4. Human review before defect filing
Candidate defects are grouped and linked to evidence, but a human reviews and approves before any Jira bug is created. The system proposes; it does not file tickets unattended.

## 5. Full traceability to source test cases
Every run, every piece of evidence, and every candidate defect links back to its originating Xray test case ID and build number. Nothing is reported or filed as a free-floating result disconnected from the case that triggered it.

## 6. Explicit, recorded preconditions
Known preconditions (account level, currency, feature flags, server time, etc.) are set deliberately for each run and the exact values applied are recorded with the evidence — never left to whatever state a shared account happens to be in. This is what makes a result reproducible.

## Source

These principles trace to direct stakeholder-interview quotes, not assumption:

- "I'd want it to flag ambiguous cases and give me reliable video/log evidence, not claim full automation." → §1, §3
- "The key result for me is whether it correctly separates 'case missing a precondition' from an actual game failure, with the video and logs attached." → §3, Req2 AC4
- "If it means setting known preconditions—account level, currency, feature flag, server time—then that's useful, but it needs to show exactly what it changed." → §6, Req4 AC2
- "When case XRAY-482 fails, I need the run result, build number, video, and grouped defect linked back to that same case." → §5, Req1 AC5, Req3 AC2
