import sqlite3
import os
import json
from datetime import datetime, timedelta
from contacts_lookup import lookup_contact  # expects contacts_lookup.py in same folder

###############################################################################
# Helpers
###############################################################################

def _convert_apple_time(ns_since_2001: int | None) -> str:
    """Convert Apple nanoseconds‑since‑2001‑01‑01 to ISO‑8601 (local time)."""
    if ns_since_2001 is None:
        return "1970-01-01T00:00:00"  # fallback
    dt = datetime(2001, 1, 1) + timedelta(seconds=ns_since_2001 / 1e9)
    return dt.isoformat(timespec="seconds")


def _digits(s: str) -> str:
    """Return only the numeric characters in *s*."""
    return "".join(ch for ch in s if ch.isdigit())

###############################################################################
# Core routine
###############################################################################

def export_conversation_to_json(
    query_name: str,
    json_path: str = "conversation.json",
    csv_path: str | None = None,
) -> str:
    """Export the **entire** 1‑to‑1 chat with *query_name* to a JSON file.

    JSON schema (list of objects):
    ```json
    {
      "timestamp": "2025-04-16T12:34:56",
      "sender": "You" | "Kamal Kapadia",
      "text": "..."
    }
    ```

    The function returns *json_path* so callers know where the file is.
    """

    # ── 1. Resolve contact phone ──────────────────────────────────────────
    phone = lookup_contact(query_name, csv_path)
    if not phone:
        raise ValueError("Contact not found in CSV")

    digits = _digits(phone)
    last10 = digits[-10:]

    # ── 2. Query iMessage DB ─────────────────────────────────────────────
    db_path = os.path.expanduser("~/Library/Messages/chat.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    sql = """
    WITH target_chat AS (
        SELECT chj.chat_id
        FROM chat_handle_join chj
        JOIN handle h ON h.rowid = chj.handle_id
        WHERE h.id = ? OR h.id LIKE ? OR h.id LIKE ? OR h.id LIKE ?
        GROUP BY chj.chat_id
        HAVING COUNT(*) = 1     -- direct chat only
        LIMIT 1
    )
    SELECT m.date,
           m.text,
           m.is_from_me
    FROM message m
    JOIN chat_message_join cmj ON cmj.message_id = m.rowid
    JOIN target_chat tc        ON tc.chat_id     = cmj.chat_id
    WHERE m.text IS NOT NULL AND m.text <> ''
    ORDER BY m.date ASC;        -- chronological
    """

    params = [phone, f"%{phone}", f"%{digits}%", f"%{last10}"]
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        raise RuntimeError("No text messages found for that direct chat.")

    contact_label = query_name.strip() or phone
    convo = [
        {
            "timestamp": _convert_apple_time(ns),
            "sender": "You" if is_from_me == 1 else contact_label,
            "text": text,
        }
        for ns, text, is_from_me in rows
    ]

    # ── 3. Write JSON ────────────────────────────────────────────────────
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(convo, f, ensure_ascii=False, indent=2)

    return json_path

###############################################################################
# CLI entry‑point
###############################################################################

if __name__ == "__main__":
    name = input("🔍 Enter the contact name to export: ").strip()
    out_file = input("💾 JSON file name [conversation.json]: ").strip() or "conversation.json"
    try:
        path = export_conversation_to_json(name, out_file)
        print(f"✅ Exported conversation to {path} ({os.path.getsize(path):,} bytes)")
    except Exception as e:
        print(f"❌ {e}")
