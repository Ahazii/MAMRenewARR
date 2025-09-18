from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
import os
import subprocess
import re
import requests

SETTINGS_FILE = os.path.join('/app/data', 'settings.json')

def load_settings():
    # Ensure data directory exists
    os.makedirs('/app/data', exist_ok=True)
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
    
    # 1. Get external IP
    try:
        ext_ip = requests.get('https://api.ipify.org', timeout=10).text.strip()
    except Exception as e:
        print(f"Error getting external IP: {e}")
        ext_ip = "Error"
    
    # 2. Get VPN IP - Multiple methods
    vpn_ip = "Not Found"

    # Method 1: Try to read from mounted log file if available
    # Expectation per deployment: From where settings.json is (/app/data), go up one dir to /app,
    # then into /binhex-qbittorrentvpn/qBittorrent/data/logs/qbittorrent.log
    # Therefore, mount the host path read-only as:
    #   -v /mnt/user/appdata/binhex-qbittorrentvpn:/app/binhex-qbittorrentvpn:ro
    # Default log path inside this container becomes:
    logpath = settings.get('qbittorrentvpn_logpath', '/app/binhex-qbittorrentvpn/qBittorrent/data/logs/qbittorrent.log')
    if os.path.exists(logpath):
        try:
            with open(logpath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Search from the end for the most recent "Detected external IP. IP:" line
            # Match IPv4 with or without surrounding quotes
            ipv4_regex = re.compile(r'Detected external IP\. IP:\s*"?([0-9]{1,3}(?:\.[0-9]{1,3}){3})"?')
            for line in reversed(lines[-500:]):  # Check last 500 lines for robustness
                m = ipv4_regex.search(line)
                if m:
                    vpn_ip = m.group(1)
                    break
        except Exception as e:
            print(f"Error reading log file {logpath}: {e}")

    # Method 2: Try alternative VPN IP detection via API if available (as a last resort)
    if vpn_ip == "Not Found":
        try:
            vpn_response = requests.get('https://ipinfo.io/json', timeout=5)
            if vpn_response.status_code == 200:
                data = vpn_response.json()
                if 'ip' in data:
                    vpn_ip = data['ip']
        except Exception as e:
            print(f"Error getting VPN IP via API: {e}")
    
    return jsonify({'external_ip': ext_ip, 'vpn_ip': vpn_ip})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
