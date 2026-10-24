# Waitlist service

Backs the "Join the waitlist" form on the landing page (`landing-page/index.html#talk`).
Stores signups in SQLite specifically so they can be queried directly — `sqlite3`,
a GUI browser, or the `/admin/waitlist` view below — rather than living in an inbox
or a third-party form provider's dashboard.

## Run locally

```sh
cd waitlist
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
WAITLIST_ADMIN_TOKEN=dev-local-token python3 app.py
# -> http://127.0.0.1:8787
```

`init_db()` runs on import, so the `waitlist.db` file and table are created
automatically on first run (gitignored — never commit it, it holds real emails).

## Endpoints

- `POST /api/waitlist` — body `{"email": "...", "name": "...", "company": "..."}`
  (JSON or form-encoded, both accepted). Returns JSON if the request is JSON or
  sends `Accept: application/json`; otherwise 303-redirects back to the referring
  page with `?waitlist=joined|existing|invalid#talk` so the no-JS form fallback
  still gets a result.
- `GET /healthz` — `{"ok": true}`, for whatever process manager/load balancer checks it.
- `GET /admin/waitlist?token=<WAITLIST_ADMIN_TOKEN>` — HTML table of all signups,
  newest first. Add `&format=csv` for a CSV download.

## Deploying (for @devops)

This is the first **live backend process** this repo has shipped — not a static
file copy like the landing page. It needs:

1. **A running process**, kept alive across reboots/crashes. Simplest: a systemd
   unit running gunicorn against `wsgi:application`, e.g.

   ```ini
   # /etc/systemd/system/witness-waitlist.service
   [Unit]
   Description=Witness waitlist service
   After=network.target

   [Service]
   WorkingDirectory=/path/to/sanityTesterTool/waitlist
   Environment=WAITLIST_ADMIN_TOKEN=<generate a real secret, don't reuse this>
   Environment=WAITLIST_DB_PATH=/var/lib/witness-waitlist/waitlist.db
   ExecStart=/path/to/venv/bin/gunicorn -w 2 -b 127.0.0.1:8787 wsgi:application
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

   `WAITLIST_DB_PATH` should point somewhere outside the repo checkout (e.g.
   `/var/lib/witness-waitlist/`) so a future `git pull`/redeploy of the static
   site never touches it.

2. **Reverse-proxy wiring**: whatever's in front of the landing page (nginx,
   Cloudflare, etc.) needs to route `/api/waitlist` and `/admin/waitlist` to
   `127.0.0.1:8787` instead of serving them as static files. Example nginx block:

   ```nginx
   location /api/ { proxy_pass http://127.0.0.1:8787; }
   location /admin/ { proxy_pass http://127.0.0.1:8787; }
   location /healthz { proxy_pass http://127.0.0.1:8787; }
   ```

   Without this, the form's `fetch('/api/waitlist')` call 404s against the static
   file server and silently falls back to a native form POST, which will also 404
   — the form won't work at all until this routing exists.

3. **A real `WAITLIST_ADMIN_TOKEN`** — generate one (`openssl rand -hex 24` or
   similar) and set it as an env var on the service, not committed anywhere. The
   token gate is a stopgap, not real auth (it's a shared secret in a URL query
   string, so it'll end up in access logs) — fine for now given there's no
   identity/access layer anywhere in this project yet, but don't treat it as
   secure against anyone who can read those logs. Rotate it if it leaks.

## Known limitations (not fixed, just named)

- No CAPTCHA/anti-bot beyond a basic honeypot field (`company_website`, hidden
  from real users via CSS) — fine for a low-traffic internal pitch page, not
  hardened against a real spam campaign.
- No rate limiting on `/api/waitlist`.
- `/admin/waitlist`'s token gate is a shared secret, not per-person auth — see
  above.

If traffic or spam ever makes these real problems, that's a reason to revisit,
not a reason this shipped wrong today.
