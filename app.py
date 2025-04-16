# app.py  — launch with:  python app.py
import os
from datetime import datetime

from flask import Flask, request, render_template_string, send_file, redirect, url_for, flash
from flask_cors import CORS
 # enable CORS for all routes


# ── your helper modules ────────────────────────────────────────────────
from find_contact_subprocess import extract_contacts_to_csv      # refresh address‑book CSV
from contacts_lookup import lookup_contact                       # name ➜ phone
from read_imessages import export_conversation_to_json           # dump chat JSON

# ---------------------------------------------------------------------
# CONFIG — tweak as needed
# ---------------------------------------------------------------------
WEBHOOK_NUMBER = "+1‑555‑867‑5309"          #  <‑‑‑ replace with your Twilio / webhook phone
CSV_PATH       = "contacts_output.csv"      #  produced by extract_contacts_to_csv
EXPORT_DIR     = "exports"                  #  iMessage json files land here

os.makedirs(EXPORT_DIR, exist_ok=True)

# ---------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "change‑me"

CORS(app) 

TEMPLATE = """
<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <title>🍏 Personal Helper</title>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@3.4.4/dist/tailwind.min.css" rel="stylesheet">
</head><body class="bg-slate-50 py-10">
<div class="max-w-xl mx-auto space-y-8">

  <div class="p-6 bg-white rounded-2xl shadow">
    <h1 class="text-2xl font-bold mb-1">📞 Webhook phone</h1>
    <p class="text-lg text-indigo-600 font-mono">{{ number }}</p>
  </div>

  <div class="p-6 bg-white rounded-2xl shadow space-y-4">
    <h2 class="text-xl font-semibold">🔄 Refresh contacts</h2>
    <form method="post" action="{{ url_for('refresh_contacts') }}">
      <button class="px-4 py-2 rounded bg-emerald-600 text-white">Pull from macOS Contacts</button>
    </form>
  </div>

  <div class="p-6 bg-white rounded-2xl shadow space-y-4">
    <h2 class="text-xl font-semibold">👤 Find a contact</h2>
    <form method="get" action="{{ url_for('lookup') }}" class="space-y-3">
      <input name="name" required placeholder="Type a name…" class="w-full p-2 border rounded">
      <button class="px-4 py-2 rounded bg-blue-600 text-white">Lookup</button>
    </form>
    {% if phone %}
      <p class="mt-2">Closest match: <b>{{ phone }}</b></p>
      <form method="post" action="{{ url_for('dump_chat', name=req_name) }}">
        <button class="mt-3 px-4 py-2 rounded bg-purple-600 text-white">Export iMessage chat ➜ JSON</button>
      </form>
    {% endif %}
  </div>

  {% if download %}
    <div class="p-6 bg-white rounded-2xl shadow">
      ✅ Conversation exported – <a class="text-indigo-700 underline" href="{{ download }}">download</a>
    </div>
  {% endif %}

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="p-4 bg-green-100 border border-green-300 rounded space-y-1">
        {% for m in messages %}<p>{{ m }}</p>{% endfor %}
      </div>
    {% endif %}
  {% endwith %}
</div></body></html>
"""

# ── routes ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(
        TEMPLATE, number=WEBHOOK_NUMBER, phone=None, req_name=None, download=None
    )

@app.post("/refresh")
def refresh_contacts():
    """Pull fresh contacts and tell the user **where** the CSV lives."""
    try:
        csv_path = extract_contacts_to_csv(CSV_PATH)  # AppleScript under the hood
        abs_path = os.path.abspath(csv_path)
        flash(f"Contacts refreshed ➜ {abs_path}. You can now search for numbers ✅")
    except Exception as e:
        flash(f"❌ {e}")
    return redirect(url_for("index"))

@app.get("/lookup")
def lookup():
    name  = request.args.get("name", "").strip()
    phone = lookup_contact(name, CSV_PATH) if name else None
    if name and not phone:
        flash("No close match found.")
    return render_template_string(
        TEMPLATE,
        number=WEBHOOK_NUMBER,
        phone=phone,
        req_name=name,
        download=None
    )

@app.post("/dump/<path:name>")
def dump_chat(name):
    try:
        ts   = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        out  = os.path.join(EXPORT_DIR, f"{name}_{ts}.json")
        export_conversation_to_json(name, out, CSV_PATH)
        return render_template_string(
            TEMPLATE,
            number=WEBHOOK_NUMBER,
            phone=None,
            req_name=None,
            download=url_for('download_file', path=os.path.basename(out))
        )
    except Exception as e:
        flash(f"❌ {e}")
        return redirect(url_for("index"))

@app.get("/d/<path:path>")
def download_file(path):
    return send_file(os.path.join(EXPORT_DIR, path), as_attachment=True)

# helper alias for Jinja
app.add_url_rule("/refresh",  'refresh_contacts', refresh_contacts)
app.add_url_rule("/dump/<path:name>", 'dump_chat', dump_chat)

# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
