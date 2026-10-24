# PC execution runner image

Container environment for design.md v6 §2.2's PC driver (Playwright is
mandatory, no off-the-shelf alternative for the PixiJS/WebGL PC target).
This is infra scaffolding, not the Execution Engine implementation —
`package.json` / `run-case.js` referenced by the Dockerfile don't exist yet
because that's build-order step 3 (@dev's territory: the actual
`run_step`/`run_case` interface from design.md §2.2), not devops's. This
Dockerfile is ready for that code to drop into once it exists; builds will
fail until then, which is expected at this stage.

Decoupled from the still-open mobile driver choice (Appium WebView-context
vs. Drizz) and from the Step-0 hands-on spike (§5 item 1) — Playwright-for-PC
is final regardless of how either of those resolves, per requirements.md
v1.4.
