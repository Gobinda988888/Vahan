from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

DEVELOPER_INFO = {
    "github": "https://www.github.com/Sudhirxd",
    "instagram": "https://www.instagram.com/sudhirxd.in",
    "name": "Sudhirxd",
    "telegram": "https://t.me/Sudhirxd",
    "website": "https://www.sudhirxd.in",
}

DESIRED_ORDER = [
    "Owner Name", "Father's Name", "Owner Serial No", "Model Name", "Maker Model",
    "Vehicle Class", "Fuel Type", "Fuel Norms", "Registration Date",
    "Insurance Company", "Insurance No", "Insurance Expiry", "Insurance Upto",
    "Fitness Upto", "Tax Upto", "PUC No", "PUC Upto", "Financier Name",
    "Registered RTO", "Address", "City Name", "Phone",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_rc(value):
    return re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()


def extract_value(soup, label):
    """Try several common HTML layouts for a label/value pair."""
    # Original layout: <div><span>Label</span><p>Value</p></div>
    for span in soup.find_all("span"):
        label_text = span.get_text(" ", strip=True).rstrip(":").strip().lower()
        if label_text == label.lower():
            parent = span.find_parent("div")
            if parent:
                value_node = parent.find("p")
                if value_node:
                    value = value_node.get_text(" ", strip=True)
                    if value and value.lower() != label.lower():
                        return value

    # Common table layout: <tr><th>Label</th><td>Value</td></tr>
    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) >= 2:
            first = cells[0].get_text(" ", strip=True).rstrip(":").strip().lower()
            if first == label.lower():
                value = cells[1].get_text(" ", strip=True)
                if value:
                    return value

    # Definition-list layout: <dt>Label</dt><dd>Value</dd>
    for dt in soup.find_all("dt"):
        if dt.get_text(" ", strip=True).rstrip(":").strip().lower() == label.lower():
            dd = dt.find_next_sibling("dd")
            if dd:
                value = dd.get_text(" ", strip=True)
                if value:
                    return value

    return None


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "Vehicle RC Intelligence Flask API",
        "developer": DEVELOPER_INFO,
        "endpoints": {
            "query_rc_param": "/api/vehicle?rc=OD19AB1234",
            "query_rc_path": "/lookup/OD19AB1234",
        },
    })


@app.route("/api/vehicle", methods=["GET"])
@app.route("/lookup/<path:rc_number>", methods=["GET"])
def vehicle_lookup(rc_number=None):
    if not rc_number:
        rc_number = (
            request.args.get("rc")
            or request.args.get("number")
            or request.args.get("code")
        )

    if not rc_number:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "message": "Parameter 'rc' is required. Example: /api/vehicle?rc=OD19AB1234",
        }), 400

    rc_clean = clean_rc(rc_number)

    # Keep this as a basic sanity check: older registrations may not have a letter series.
    if not re.fullmatch(r"[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{1,4}", rc_clean):
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "rc": rc_clean,
            "message": "RC format looks invalid. Example: OD19AB1234 or an older format such as OD195040.",
        }), 400

    target_url = f"https://vahanx.in/rc-search/{rc_clean}"

    try:
        response = requests.get(
            target_url,
            headers=HEADERS,
            timeout=(5, 20),
            allow_redirects=True,
        )
        if response.status_code == 404:
            return jsonify({
                "status": "error",
                "developer": DEVELOPER_INFO,
                "rc": rc_clean,
                "message": "The source site returned 404 for this RC. The record may be unavailable, or the source URL may have changed.",
            }), 404

        response.raise_for_status()
    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "rc": rc_clean,
            "message": "The vehicle data source timed out. Please retry later.",
        }), 504
    except requests.exceptions.RequestException as exc:
        app.logger.warning("Vehicle source request failed for %s: %s", rc_clean, exc)
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "rc": rc_clean,
            "message": "Could not retrieve data from the vehicle source.",
            "details": str(exc),
        }), 502

    soup = BeautifulSoup(response.text, "html.parser")
    data = {}

    for key in DESIRED_ORDER:
        value = extract_value(soup, key)
        if value:
            data[key] = value

    if data:
        return jsonify({
            "status": "success",
            "developer": DEVELOPER_INFO,
            "rc": rc_clean,
            "data": data,
        }), 200

    # Helpful diagnostics without returning the entire upstream page.
    page_title = soup.title.get_text(" ", strip=True) if soup.title else None
    page_text = soup.get_text(" ", strip=True)
    blocked_hint = any(
        marker in page_text.lower()
        for marker in ("access denied", "captcha", "verify you are human", "blocked")
    )

    app.logger.warning(
        "No fields extracted for RC %s; upstream_status=%s; title=%r; html_bytes=%s",
        rc_clean, response.status_code, page_title, len(response.text)
    )

    if blocked_hint:
        message = "The source site appears to have returned a block or verification page; no vehicle details were extracted."
    elif len(page_text) < 100:
        message = "The source returned an almost-empty page; it may require JavaScript or may be temporarily unavailable."
    else:
        message = "The source page loaded, but no expected vehicle fields were found. The page structure may have changed or details may require JavaScript."

    return jsonify({
        "status": "error",
        "developer": DEVELOPER_INFO,
        "rc": rc_clean,
        "message": message,
        "source_http_status": response.status_code,
        "source_page_title": page_title,
    }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
    
