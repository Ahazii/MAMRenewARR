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
    logpath = settings.get('qbittorrentvpn_logpath', '/shared/qbittorrent/logs/qbittorrent.log')
    if os.path.exists(logpath):
        try:
            with open(logpath, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-100:]):  # Check last 100 lines
                    m = re.search(r'Detected external IP\. IP: "([0-9\.]+)"', line)
                    if m:
                        vpn_ip = m.group(1)
                        break
        except Exception as e:
            print(f"Error reading log file {logpath}: {e}")
    
    # Method 2: Try alternative VPN IP detection via API if available
    if vpn_ip == "Not Found":
        try:
            # Try common VPN detection services
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
