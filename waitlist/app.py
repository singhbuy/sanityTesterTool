"""Waitlist signup service for the Witness landing page.

Stores signups in SQLite so they can be queried directly (sqlite3 CLI, a
GUI browser, or the /admin/waitlist view below) instead of living in an
inbox or a form-provider's dashboard.
"""
import csv
import io
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, g, jsonify, redirect, request
from markupsafe import escape

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("WAITLIST_DB_PATH", str(BASE_DIR / "waitlist.db"))
SCHEMA_PATH = BASE_DIR / "schema.sql"
ADMIN_TOKEN = os.environ.get("WAITLIST_ADMIN_TOKEN")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
    finally:
        conn.close()


def wants_json() -> bool:
    if request.is_json:
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept and "text/html" not in accept


def redirect_with_result(result: str):
    target = request.referrer or "/"
    # strip any existing query string the referrer might carry, then append ours
    base = target.split("?", 1)[0].split("#", 1)[0]
    return redirect(f"{base}?waitlist={result}#talk", code=303)


@app.post("/api/waitlist")
def join_waitlist():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip()
    name = (data.get("name") or "").strip() or None
    company = (data.get("company") or "").strip() or None
    honeypot = (data.get("company_website") or "").strip()
    source = (data.get("source") or "landing-page").strip()[:64]

    # Honeypot: real users never see or fill this field. Pretend success
    # so the bot doesn't learn its submission was rejected.
    if honeypot:
        return jsonify({"ok": True, "status": "new"}) if wants_json() else redirect_with_result("joined")

    if not email or not EMAIL_RE.match(email):
        return (
            (jsonify({"ok": False, "error": "invalid_email"}), 400)
            if wants_json()
            else redirect_with_result("invalid")
        )

    db = get_db()
    try:
        db.execute(
            "INSERT INTO waitlist (email, name, company, source) VALUES (?, ?, ?, ?)",
            (email, name, company, source),
        )
        db.commit()
        status = "new"
    except sqlite3.IntegrityError:
        status = "existing"

    return jsonify({"ok": True, "status": status}) if wants_json() else redirect_with_result(
        "joined" if status == "new" else "existing"
    )


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})


def _require_admin():
    if not ADMIN_TOKEN:
        return Response("Admin view disabled: WAITLIST_ADMIN_TOKEN is not set.", status=503)
    if request.args.get("token") != ADMIN_TOKEN:
        return Response("Forbidden.", status=403)
    return None


@app.get("/admin/waitlist")
def admin_waitlist():
    denied = _require_admin()
    if denied is not None:
        return denied

    db = get_db()
    rows = db.execute(
        "SELECT email, name, company, source, created_at FROM waitlist ORDER BY created_at DESC"
    ).fetchall()

    if request.args.get("format") == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["email", "name", "company", "source", "created_at"])
        for row in rows:
            writer.writerow([row["email"], row["name"], row["company"], row["source"], row["created_at"]])
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=waitlist.csv"},
        )

    token = escape(request.args.get("token", ""))
    body_rows = "\n".join(
        f"<tr><td>{escape(r['email'])}</td><td>{escape(r['name'] or '')}</td>"
        f"<td>{escape(r['company'] or '')}</td><td>{escape(r['source'])}</td>"
        f"<td>{escape(r['created_at'])}</td></tr>"
        for r in rows
    )
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Waitlist — {len(rows)} signups</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; background:#10131A; color:#EDEAE2; padding: 24px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 6px 12px; border-bottom: 1px solid #2B303B; }}
  th {{ color: #9196A1; font-weight: 500; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.06em; }}
  a {{ color: #54C2B2; }}
  .meta {{ color: #9196A1; font-size: 0.82rem; margin-bottom: 16px; }}
</style></head>
<body>
  <h1>Waitlist &mdash; {len(rows)} signups</h1>
  <p class="meta">Generated {generated_at}. <a href="/admin/waitlist?token={token}&format=csv">Download CSV</a>.
  This view is gated by a shared token in the URL, not real auth &mdash; treat the link as a secret and rotate it
  if it leaks. Direct sqlite3 access to the db file works too: this is a convenience view, not the only way in.</p>
  <table>
    <tr><th>Email</th><th>Name</th><th>Company</th><th>Source</th><th>Joined (UTC)</th></tr>
    {body_rows}
  </table>
</body></html>"""
    return Response(html, mimetype="text/html")


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8787)))
