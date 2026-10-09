import os
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

DEVELOPER_INFO = {
    "github": "https://www.github.com/Sudhirxd",
    "instagram": "https://www.instagram.com/sudhirxd.in",
    "name": "Sudhirxd",
    "telegram": "https://t.me/Sudhirxd",
    "website": "https://www.sudhirxd.in"
}

# Known labels present on VahanX vehicle card
TARGET_LABELS = {
    "modal name": "Model Name",
    "model name": "Model Name",
    "owner name": "Owner Name",
    "code": "RTO Code",
    "city name": "City Name",
    "phone": "Phone",
    "website": "Website",
    "address": "Address",
    "vehicle class": "Vehicle Class",
    "fuel type": "Fuel Type",
    "registration date": "Registration Date",
    "insurance upto": "Insurance Upto",
    "fitness upto": "Fitness Upto",
    "puc upto": "PUC Upto"
}

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "service": "Vehicle RC API",
        "endpoints": {
            "api": "/api/vehicle?rc=OD195040"
        }
    })

@app.route('/api/vehicle', methods=['GET'])
def vehicle_lookup():
    rc_number = request.args.get('rc') or request.args.get('number')
    if not rc_number:
        return jsonify({"status": "error", "message": "rc parameter missing"}), 400

    rc_clean = re.sub(r'[^A-Za-z0-9]', '', str(rc_number)).upper()
    target_url = f"https://vahanx.in/rc-search/{rc_clean}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=15)
        if res.status_code == 404:
            return jsonify({"status": "error", "message": f"RC {rc_clean} not found"}), 404

        soup = BeautifulSoup(res.text, "html.parser")
        data = {}

        # 1. Target labels ko dhoondo (Modal Name, Owner Name, etc.)
        for element in soup.find_all(True):
            text = element.get_text(strip=True).lower()
            if text in TARGET_LABELS:
                std_key = TARGET_LABELS[text]
                
                # Check previous sibling for the actual value (Hero HF Deluxe etc.)
                prev_sibling = element.find_previous_sibling()
                if prev_sibling and prev_sibling.get_text(strip=True):
                    val = prev_sibling.get_text(strip=True)
                    if val.lower() != text and len(val) > 1:
                        data[std_key] = val
                        continue
                
                # Check parent container children
                parent = element.parent
                if parent:
                    children = [c for c in parent.find_all(recursive=False) if c.get_text(strip=True)]
                    for i, child in enumerate(children):
                        if child == element and i > 0:
                            val = children[i - 1].get_text(strip=True)
                            if val.lower() != text:
                                data[std_key] = val
                                break

        # Filter out FAQ / irrelevant text
        data = {k: v for k, v in data.items() if not k.startswith("Q.") and "vahanx" not in v.lower()}

        if data:
            return jsonify({
                "status": "success",
                "developer": DEVELOPER_INFO,
                "rc": rc_clean,
                "data": data
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"Could not extract vehicle data for RC: {rc_clean}"
            }), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
