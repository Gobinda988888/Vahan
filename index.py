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

TARGET_LABELS = [
    "Modal Name", "Model Name", "Owner Name", "Code", "City Name", 
    "Phone", "Website", "Address", "Vehicle Class", "Fuel Type",
    "Registration Date", "Insurance Upto", "Fitness Upto", "PUC Upto"
]

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "service": "Vehicle RC Intelligence Flask API",
        "developer": DEVELOPER_INFO,
        "endpoints": {
            "query_rc_param": "/api/vehicle?rc=OD195040",
            "query_rc_path": "/lookup/OD195040"
        }
    })

@app.route('/api/vehicle', methods=['GET'])
@app.route('/lookup/<path:rc_number>', methods=['GET'])
def vehicle_lookup(rc_number=None):
    if not rc_number:
        rc_number = request.args.get('rc') or request.args.get('number') or request.args.get('code')
    
    if not rc_number:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "message": "Parameter 'rc' is required. Example: /api/vehicle?rc=OD195040"
        }), 400

    rc_clean = re.sub(r'[^A-Za-z0-9]', '', str(rc_number)).upper()
    
    if len(rc_clean) < 4:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "message": "Invalid RC registration number format."
        }), 400

    target_url = f"https://vahanx.in/rc-search/{rc_clean}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=15)
        if res.status_code == 404:
            return jsonify({
                "status": "error",
                "developer": DEVELOPER_INFO,
                "message": f"No vehicle registration record found for RC: {rc_clean}"
            }), 404

        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "message": f"Network error: {str(e)}"
        }), 502

    data = {}

    for label_name in TARGET_LABELS:
        # Aisa element jiska text label_name se match kare (case-insensitive)
        label_elem = soup.find(lambda el: el.name in ['span', 'p', 'div', 'h3', 'h4', 'small'] and el.get_text(strip=True).lower() == label_name.lower())
        
        if label_elem:
            # 1. Check previous sibling (kyunki value label ke upar hai)
            prev = label_elem.find_previous_sibling()
            if prev and prev.get_text(strip=True):
                data[label_name] = prev.get_text(strip=True)
                continue

            # 2. Check parent div ke elements
            parent = label_elem.parent
            if parent:
                children = [c for c in parent.find_all(recursive=False) if c.get_text(strip=True)]
                if len(children) >= 2:
                    # Agar label doosra element hai, pehla element value hai
                    for i, child in enumerate(children):
                        if child == label_elem and i > 0:
                            data[label_name] = children[i-1].get_text(strip=True)
                            break

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
            "developer": DEVELOPER_INFO,
            "message": f"Could not parse vehicle details for RC: {rc_clean}"
        }), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    
