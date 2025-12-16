import os
from datetime import datetime, timezone
import requests
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

EVOCON_AUTH = os.getenv("EVOCON_AUTH")  # Base64(user:password)
EVOCON_URL = "https://api.evocon.com/api/checklists/9897e575-882a-40f3-ad1e-1aad4577dafa"

HTML = """
<!doctype html>
<html lang="el">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Checklist Post</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 24px; }
    .card { max-width: 520px; padding: 16px; border: 1px solid #ddd; border-radius: 12px; }
    label { display:block; margin: 12px 0 6px; }
    input, select, button { width: 100%; padding: 10px; font-size: 16px; }
    button { margin-top: 14px; cursor: pointer; }
    small { color:#666; }
  </style>
</head>
<body>
  <div class="card">
    <h2>ΠΑΛΕΤΑ — Post to Evocon</h2>

    <form method="POST" action="/submit">
      <label for="value">Value (Element id=1)</label>
      <input id="value" name="value" type="number" step="any" required placeholder="e.g. 12" />

      <label for="stationId">Station</label>
      <select id="stationId" name="stationId" required>
        <option value="2" selected>2</option>
        <option value="1">1</option>
        <option value="3">3</option>
      </select>

      <label for="description">Description (optional)</label>
      <input id="description" name="description" type="text" placeholder="optional note" />

      <small>It will POST to Evocon checklistId 9897e575-882a-40f3-ad1e-1aad4577dafa</small>

      <button type="submit">POST to Evocon</button>
    </form>
  </div>
</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(HTML)

def now_iso_with_offset():
    # Evocon accepts ISO with timezone; easiest is UTC "Z".
    return datetime.now(timezone.utc).isoformat()

@app.post("/submit")
def submit():
    if not EVOCON_AUTH:
        return jsonify({"error": "Missing EVOCON_AUTH env var (Base64 user:password)"}), 500

    raw_value = request.form.get("value", "").strip()
    station_id = request.form.get("stationId", "").strip()
    description = request.form.get("description", "").strip()

    # Hard truth: if you don’t validate, you’ll post garbage and blame the API.
    try:
        value = float(raw_value)
    except ValueError:
        return jsonify({"error": f"Invalid value: {raw_value}"}), 400

    payload = {
        "checklistId": "9897e575-882a-40f3-ad1e-1aad4577dafa",
        "description": description,
        "eventTimeISO": now_iso_with_offset(),
        "elements": [
            {"id": "1", "value": value}
        ],
        "stationId": str(station_id),
        "name": "ΠΑΛΕΤΑ"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {EVOCON_AUTH}",
    }

    r = requests.post(EVOCON_URL, json=payload, headers=headers, timeout=15)

    # Return EVERYTHING needed to debug fast (status, payload, Evocon response)
    return jsonify({
        "posted_to": EVOCON_URL,
        "status_code": r.status_code,
        "payload_sent": payload,
        "evocon_response_text": r.text
    }), r.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
