from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
import os
import subprocess
import re
import requests

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_settings(data):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('basic'))

@app.route('/basic')
def basic():
    return render_template('basic.html')

@app.route('/advanced')
def advanced():
    return render_template('advanced.html')

@app.route('/config')
def config():
    return render_template('config.html')

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    return jsonify(load_settings())

@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    data = request.json
    save_settings(data)
    return jsonify({'status': 'ok'})

@app.route('/api/get_ips', methods=['GET'])
def api_get_ips():
    settings = load_settings()
    container = settings.get('qbittorrentvpn_container', 'binhex-qbittorrentvpn')
    logpath = settings.get('qbittorrentvpn_logpath', '/config/QBittorrent/data/logs/qbittorrent.log')
    # 1. Get external IP
    try:
        ext_ip = requests.get('https://api.ipify.org').text.strip()
    except Exception:
        ext_ip = None
    # 2. Get VPN IP from log file inside container
    vpn_ip = None
    try:
        result = subprocess.run([
            'docker', 'exec', container, 'cat', logpath
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in reversed(lines):
                m = re.search(r'Detected external IP\. IP: "([0-9\.]+)"', line)
                if m:
                    vpn_ip = m.group(1)
                    break
        else:
            print(f"Error reading log: {result.stderr}")
    except Exception as e:
        print(f"Exception: {e}")
    return jsonify({'external_ip': ext_ip, 'vpn_ip': vpn_ip})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
