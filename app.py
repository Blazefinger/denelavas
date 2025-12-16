import os
from datetime import datetime, timezone

import requests
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

EVOCON_AUTH = os.getenv("EVOCON_AUTH")  # Base64(username:password) WITHOUT "Basic "
CHECKLIST_ID = os.getenv("EVOCON_CHECKLIST_ID", "9897e575-882a-40f3-ad1e-1aad4577dafa")
STATION_ID = os.getenv("EVOCON_STATION_ID", "2")
CHECKLIST_NAME = os.getenv("EVOCON_CHECKLIST_NAME", "ΠΑΛΕΤΑ")
PALLET_ELEMENT_ID = os.getenv("EVOCON_PALLET_ELEMENT_ID", "2")  # change if needed

EVOCON_URL = f"https://api.evocon.com/api/checklists/{CHECKLIST_ID}"

HTML = r"""
<!doctype html>
<html lang="el">
<head>
<meta charset="utf-8">
<title>Denelpack Pallet Label</title>

<style>
  @page { size: A4; margin: 0; }

  body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: white;
  }

  .sheet {
    width: 210mm;
    height: 297mm;
    padding: 10mm;
    box-sizing: border-box;
  }

  .row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1.2fr;
    border-top: 2px solid #000;
    border-bottom: 2px solid #000;
    padding: 6mm 0;
  }

  .cell .label {
    font-size: 12px;
    font-weight: 700;
  }

  .cell .value {
    font-size: 34px;
    font-weight: 900;
    margin-top: 2mm;
  }

  .date .value {
    font-size: 54px;
    text-align: center;
  }

  .mid {
    display: grid;
    grid-template-columns: 1fr 0.8fr;
    margin-top: 6mm;
    border-bottom: 2px solid #000;
    padding-bottom: 6mm;
  }

  .leftGrid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6mm;
  }

  .small {
    font-size: 18px;
    font-weight: 800;
  }

  .palletInput {
    font-size: 56px;
    font-weight: 900;
    border: none;
    outline: none;
    background: transparent;
    width: 140px;
  }

  .title {
    font-size: 54px;
    font-weight: 900;
    margin: 10mm 0;
  }

  .weights {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10mm;
    border-top: 2px solid #000;
    padding-top: 6mm;
  }

  .weights h3 {
    font-size: 28px;
    font-weight: 900;
    margin-bottom: 6mm;
  }

  .big {
    font-size: 46px;
    font-weight: 900;
  }

  /* Submit button visible on screen */
  .submitBtn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    font-size: 18px;
    padding: 12px 24px;
    cursor: pointer;
  }

  /* Hide submit button when printing */
  @media print {
    .submitBtn { display: none; }
  }
</style>
</head>

<body>

<!-- THIS form submission is what triggers the POST to Evocon -->
<form method="POST" action="/submit">

<div class="sheet">

  <!-- TOP -->
  <div class="row">
    <div class="cell">
      <div class="label">FILM TYPE</div>
      <div class="value">DS</div>
    </div>
    <div class="cell">
      <div class="label">THICKNESS</div>
      <div class="value">23MI</div>
    </div>
    <div class="cell">
      <div class="label">WIDTH</div>
      <div class="value">500mm</div>
    </div>
    <div class="cell date">
      <div class="label">DATE</div>
      <div class="value">4/11/2025</div>
    </div>
  </div>

  <!-- LOT -->
  <div class="row" style="grid-template-columns:1fr 0.6fr 1fr 1.2fr;">
    <div class="cell">
      <div class="label">LOT NUMBER</div>
      <div class="small">00011900</div>
    </div>
    <div class="cell">
      <div class="label">&nbsp;</div>
      <div class="small">A</div>
    </div>
    <div class="cell">
      <div class="label">BARCODE</div>
      <div class="small">SD 2</div>
    </div>
    <div class="cell"></div>
  </div>

  <!-- MID -->
  <div class="mid">
    <div>
      <div class="leftGrid">
        <div>
          <div class="label">PALLET TYPE</div>
          <div class="small">80/120</div>
        </div>
        <div>
          <div class="label">ROLLS/PAL</div>
          <div class="small">16</div>
        </div>
        <div></div>

        <div>
          <div class="label">ΒΑΡΔΙΑ</div>
          <div class="small">A</div>
        </div>
        <div>
          <div class="label">OPERATOR</div>
          <div class="small">SD</div>
        </div>
        <div>
          <div class="label">CORE WEIGHT</div>
          <div class="small">2 KG</div>
        </div>

        <!-- PALLET NO INPUT (this is what you post to Evocon) -->
        <div style="grid-column:1 / span 2;">
          <div class="label">PALLET No</div>
          <input name="pallet_no" type="number" class="palletInput" value="28" required>
        </div>
      </div>
    </div>

    <!-- Icons placeholder (kept same) -->
    <div style="display:flex;align-items:center;justify-content:center;font-weight:900;">
      ICONS
    </div>
  </div>

  <!-- PRODUCT -->
  <div class="title">DS 23M JUMBO ECO</div>

  <!-- WEIGHTS -->
  <div class="weights">
    <div>
      <h3>NET WEIGHT</h3>
      <div class="big">#VALUE! KG</div>
    </div>
    <div>
      <h3>GROSS WEIGHT</h3>
      <div class="big">ΠΑΛΕΤΑ KG</div>
    </div>
  </div>

</div>

<!-- THIS BUTTON triggers the form submit => /submit => POST to Evocon API -->
<button class="submitBtn" type="submit">POST TO EVOCON</button>

</form>

</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(HTML)

@app.post("/submit")
def submit():
    if not EVOCON_AUTH:
        return jsonify({
            "error": "EVOCON_AUTH missing. Set it in Railway Variables as Base64(username:password) WITHOUT 'Basic '"
        }), 500

    pallet_no_raw = (request.form.get("pallet_no") or "").strip()
    try:
        pallet_no = int(pallet_no_raw)
    except ValueError:
        return jsonify({"error": f"Invalid pallet_no: {pallet_no_raw}"}), 400

    payload = {
        "checklistId": CHECKLIST_ID,
        "description": "",
        "eventTimeISO": datetime.now(timezone.utc).isoformat(),
        "elements": [
            {"id": str(PALLET_ELEMENT_ID), "value": pallet_no}
        ],
        "stationId": str(STATION_ID),
        "name": CHECKLIST_NAME
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {EVOCON_AUTH}",
    }

    try:
        r = requests.post(EVOCON_URL, json=payload, headers=headers, timeout=15)
    except requests.RequestException as e:
        return jsonify({
            "error": "Failed to reach Evocon",
            "details": str(e),
            "url": EVOCON_URL,
            "payload_sent": payload
        }), 502

    return jsonify({
        "posted_to": EVOCON_URL,
        "status_code": r.status_code,
        "payload_sent": payload,
        "evocon_response_text": r.text
    }), r.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
