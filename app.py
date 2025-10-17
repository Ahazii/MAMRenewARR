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
    debug_info = []
    
    # 1. Get external IP
    try:
        ext_ip = requests.get('https://api.ipify.org', timeout=10).text.strip()
        debug_info.append(f"External IP: {ext_ip}")
    except Exception as e:
        print(f"Error getting external IP: {e}")
        ext_ip = "Error"
        debug_info.append(f"External IP Error: {e}")
    
    # 2. Get VPN IP - Enhanced debugging
    vpn_ip = "Not Found"
    debug_info.append("=== VPN IP Detection Debug ===")
    
    # Method 1: Try to read from mounted log/text file
    logpath = settings.get('qbittorrentvpn_logpath', '/app/shared/qbittorrent-logs/qbittorrent.log')
    debug_info.append(f"Configured log path: {logpath}")
    debug_info.append(f"File exists: {os.path.exists(logpath)}")
    
    if os.path.exists(logpath):
        try:
            debug_info.append(f"File size: {os.path.getsize(logpath)} bytes")
            with open(logpath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            debug_info.append(f"Total lines in file: {len(lines)}")
            
            # Multiple search patterns for different log formats
            patterns = [
                # qBittorrent VPN log pattern
                re.compile(r'Detected external IP\. IP:\s*"?([0-9]{1,3}(?:\.[0-9]{1,3}){3})"?'),
                # Alternative patterns for VPN IP
                re.compile(r'VPN IP:\s*([0-9]{1,3}(?:\.[0-9]{1,3}){3})'),
                re.compile(r'Current IP:\s*([0-9]{1,3}(?:\.[0-9]{1,3}){3})'),
                re.compile(r'Public IP:\s*([0-9]{1,3}(?:\.[0-9]{1,3}){3})'),
                # Generic IP pattern (last resort)
                re.compile(r'([0-9]{1,3}(?:\.[0-9]{1,3}){3})')
            ]
            
            # Search from the end for the most recent IP
            search_lines = lines[-500:] if len(lines) > 500 else lines
            debug_info.append(f"Searching last {len(search_lines)} lines")
            
            found_ips = []
            for i, pattern in enumerate(patterns):
                for line_idx, line in enumerate(reversed(search_lines)):
                    m = pattern.search(line)
                    if m:
                        candidate_ip = m.group(1)
                        # Skip localhost and internal IPs for most patterns
                        if i < len(patterns) - 1:  # For specific patterns, be picky
                            if not (candidate_ip.startswith('127.') or 
                                   candidate_ip.startswith('192.168.') or 
                                   candidate_ip.startswith('10.') or 
                                   candidate_ip.startswith('172.')):
                                found_ips.append((candidate_ip, f"Pattern {i+1}", line.strip()))
                        else:  # For generic pattern, accept any IP
                            found_ips.append((candidate_ip, f"Pattern {i+1}", line.strip()))
                        
                        if len(found_ips) >= 5:  # Limit results
                            break
                if found_ips:
                    break
            
            if found_ips:
                vpn_ip = found_ips[0][0]  # Use the first (most recent) match
                debug_info.append(f"Found IPs: {found_ips[:3]}")
            else:
                debug_info.append("No IP patterns matched")
                # Show last few lines for debugging
                debug_info.append("Last 3 lines:")
                for line in search_lines[-3:]:
                    debug_info.append(f"  {line.strip()}")
                    
        except Exception as e:
            error_msg = f"Error reading log file {logpath}: {e}"
            print(error_msg)
            debug_info.append(error_msg)
    else:
        # List what files/directories are available for debugging
        try:
            parent_dir = os.path.dirname(logpath)
            if os.path.exists(parent_dir):
                files = os.listdir(parent_dir)
                debug_info.append(f"Files in {parent_dir}: {files[:10]}")
            else:
                debug_info.append(f"Parent directory {parent_dir} does not exist")
                # Try to find any mounted volumes
                if os.path.exists('/app'):
                    app_contents = os.listdir('/app')
                    debug_info.append(f"Contents of /app: {app_contents}")
        except Exception as e:
            debug_info.append(f"Error listing directory: {e}")

    # Method 2: Only use API fallback if explicitly enabled or no file found
    if vpn_ip == "Not Found" and not os.path.exists(logpath):
        debug_info.append("Falling back to API detection (file not found)")
        try:
            vpn_response = requests.get('https://ipinfo.io/json', timeout=5)
            if vpn_response.status_code == 200:
                data = vpn_response.json()
                if 'ip' in data:
                    vpn_ip = data['ip']
                    debug_info.append(f"API returned: {vpn_ip}")
        except Exception as e:
            debug_info.append(f"API fallback error: {e}")
    
    # Print debug info to container logs
    print("\n".join(debug_info))
    
    return jsonify({
        'external_ip': ext_ip, 
        'vpn_ip': vpn_ip,
        'debug_info': debug_info[-10:]  # Include last 10 debug messages in response
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
