# Landing page — "Witness"

Pitch page for QA/engineering leadership evaluating adoption. Content is pulled
directly from [`specs/constitution.md`](../specs/constitution.md)'s Source
section (real stakeholder-interview quotes) and
[`specs/requirements.md`](../specs/requirements.md) — see `index.html` for the
mapping of each claim back to its constitution principle / requirement AC.

Live, rendered copy (updates independently of this file):
https://claude.ai/artifact/ND49iKXJrYixSvzhfF8amB

`index.html` here is a static, standalone copy for version control — open it
directly in a browser, no build step.

## Waitlist form

The closing "Join the waitlist" form POSTs to `/api/waitlist`, served by the
backend in [`../waitlist/`](../waitlist/) — see that directory's README for
how to run it and what the live deployment needs (a running process + reverse
proxy wiring, not just a static file copy). Without that backend deployed and
routed, the form 404s. The Claude Artifact copy above does **not** have the
backend behind it, so the form won't work there — it's static-page-only.
