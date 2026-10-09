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

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "service": "Vehicle RC API",
        "debug_url": "/debug/rc?num=OD195040",
        "api_url": "/api/vehicle?rc=OD195040"
    })

# 👉 BROWSER ME INSPECT KARNE KE LIYE YEH ENDPOINT HAI
@app.route('/debug/rc', methods=['GET'])
def debug_inspect():
    rc_number = request.args.get('num') or request.args.get('rc') or "OD195040"
    rc_clean = re.sub(r'[^A-Za-z0-9]', '', str(rc_number)).upper()
    
    target_url = f"https://vahanx.in/rc-search/{rc_clean}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        matches = {}
        for term in ["HERO HF DELUXE", "Model Name", "Modal Name", "City Name", "Angul", "Owner Name"]:
            pos = res.text.lower().find(term.lower())
            if pos >= 0:
                snippet = res.text[max(0, pos - 150): min(len(res.text), pos + 350)]
                matches[term] = snippet.replace("\n", " ").strip()
            else:
                matches[term] = "NOT FOUND IN RAW HTML"

        return jsonify({
            "status_code": res.status_code,
            "html_length": len(res.text),
            "page_title": soup.title.get_text(" ", strip=True) if soup.title else "No title",
            "search_snippets": matches,
            "preview_first_500_chars": res.text[:500]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vehicle', methods=['GET'])
def vehicle_lookup():
    rc_number = request.args.get('rc') or request.args.get('number')
    if not rc_number:
        return jsonify({"status": "error", "message": "rc parameter missing"}), 400

    rc_clean = re.sub(r'[^A-Za-z0-9]', '', str(rc_number)).upper()
    target_url = f"https://vahanx.in/rc-search/{rc_clean}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        data = {}

        # Generic Card / Div Parser
        for block in soup.find_all(['div', 'li']):
            texts = [t.strip() for t in block.stripped_strings]
            if len(texts) == 2:
                # Text[0] = Value, Text[1] = Label
                if any(lbl in texts[1].lower() for lbl in ['name', 'code', 'city', 'phone', 'website', 'address']):
                    data[texts[1]] = texts[0]

        if data:
            return jsonify({"status": "success", "rc": rc_clean, "data": data})
        return jsonify({"status": "error", "message": f"Could not parse vehicle details for RC: {rc_clean}"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
