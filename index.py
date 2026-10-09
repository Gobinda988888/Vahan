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
        "endpoint": "/api/vehicle?rc=OD195040"
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

        # Har block ko check karein jisme label aur value pair ho
        for container in soup.find_all(['div', 'li']):
            # Sirf direct textual lines extract karein
            lines = [t.strip() for t in container.stripped_strings if t.strip()]
            
            # Jab container me theek 2 text elements hon (Line 0 = Value, Line 1 = Label)
            if len(lines) == 2:
                val, lbl = lines[0], lines[1]
                lbl_lower = lbl.lower()
                
                if lbl_lower in TARGET_LABELS:
                    clean_key = TARGET_LABELS[lbl_lower]
                    if val.lower() != lbl_lower and len(val) > 1:
                        data[clean_key] = val

            # Agar label pehle aur value baad me ho (Line 0 = Label, Line 1 = Value)
            elif len(lines) == 2:
                lbl, val = lines[0], lines[1]
                lbl_lower = lbl.lower()
                if lbl_lower in TARGET_LABELS:
                    clean_key = TARGET_LABELS[lbl_lower]
                    if val.lower() != lbl_lower and len(val) > 1:
                        data[clean_key] = val

        # Clean-up table unwanted headers like "State / UT"
        if data.get("RTO Code") == "State / UT":
            data.pop("RTO Code", None)

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
                "message": f"Could not parse vehicle details for RC: {rc_clean}"
            }), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
