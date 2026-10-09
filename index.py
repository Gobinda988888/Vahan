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
    "website": "https://www.sudhirxd.in"
}

DESIRED_ORDER = [
    "Owner Name", "Father's Name", "Owner Serial No", "Model Name", "Maker Model",
    "Vehicle Class", "Fuel Type", "Fuel Norms", "Registration Date", "Insurance Company",
    "Insurance No", "Insurance Expiry", "Insurance Upto", "Fitness Upto", "Tax Upto",
    "PUC No", "PUC Upto", "Financier Name", "Registered RTO", "Address", "City Name", "Phone"
]

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "service": "Vehicle RC Intelligence Flask API",
        "developer": DEVELOPER_INFO,
        "endpoints": {
            "query_rc_param": "/api/vehicle?rc=BR03H5690",
            "query_rc_path": "/lookup/BR03H5690"
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
            "message": "Parameter 'rc' is required. Example: /api/vehicle?rc=BR03H5690"
        }), 400

    # Clean and uppercase RC number
    rc_clean = re.sub(r'[^A-Za-z0-9]', '', str(rc_number)).upper()
    
    if len(rc_clean) < 4:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "message": "Invalid RC registration number format."
        }), 400

    target_url = f"https://vahanx.in/rc-search/{rc_clean}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=12)
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
            "message": f"Network error communicating with Vahan portal: {str(e)}"
        }), 502

    data = {}
    for key in DESIRED_ORDER:
        try:
            span = soup.find("span", string=key)
            if span:
                div = span.find_parent("div")
                if div and div.find("p"):
                    val = div.find("p").get_text(strip=True)
                    if val:
                        data[key] = val
        except Exception:
            pass

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
            "message": f"No vehicle details found or invalid RC number: {rc_clean}"
        }), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
