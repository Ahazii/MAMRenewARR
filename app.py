from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
import os
import subprocess
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

# Global session for MAM operations
mam_session = None

def get_mam_session():
    """Get or create a requests session for MAM with proper headers"""
    global mam_session
    if mam_session is None:
        mam_session = requests.Session()
        
        # More realistic browser headers
        mam_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Add retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        mam_session.mount("http://", adapter)
        mam_session.mount("https://", adapter)
    return mam_session

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

@app.route('/api/login_mam', methods=['POST'])
def api_login_mam():
    """Login to MyAnonamouse using stored credentials"""
    settings = load_settings()
    debug_info = []
    
    # Get credentials from settings
    mam_url = settings.get('mam_url', 'https://www.myanonamouse.net/')
    username = settings.get('mam_username', '')
    password = settings.get('mam_password', '')
    
    debug_info.append(f"MAM URL: {mam_url}")
    debug_info.append(f"Username provided: {'Yes' if username else 'No'}")
    debug_info.append(f"Password provided: {'Yes' if password else 'No'}")
    
    if not username or not password:
        return jsonify({
            'success': False, 
            'message': 'MAM username or password not configured. Please check your settings.',
            'debug_info': debug_info
        })
    
    try:
        session = get_mam_session()
        
        # First, visit the main page to establish cookies like a real browser would
        main_url = mam_url.rstrip('/')
        debug_info.append(f"Visiting main page first: {main_url}")
        main_response = session.get(main_url, timeout=10)
        debug_info.append(f"Main page status: {main_response.status_code}")
        
        # Check cookies after main page visit
        initial_cookies = [cookie.name for cookie in session.cookies]
        debug_info.append(f"Cookies after main page: {', '.join(initial_cookies) if initial_cookies else 'None'}")
        
        # Check cookies after main page visit
        initial_cookies = [cookie.name for cookie in session.cookies]
        debug_info.append(f"Cookies after main page: {', '.join(initial_cookies) if initial_cookies else 'None'}")
        
        # Add a small delay to appear more human-like
        import time
        time.sleep(1)
        
        # Now get the login page to check if we need to login
        login_url = mam_url.rstrip('/') + '/login.php'
        debug_info.append(f"Accessing login URL: {login_url}")
        
        # Update headers for the login page request
        login_headers = {
            'Referer': main_url,
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        }
        
        response = session.get(login_url, headers=login_headers, timeout=10)
        
        debug_info.append(f"Login page status: {response.status_code}")
        debug_info.append(f"Final URL after redirects: {response.url}")
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'message': f'Failed to access MAM login page. Status: {response.status_code}',
                'debug_info': debug_info
            })
        
        # Simple login detection: if we access main page and DON'T get redirected to login.php, we're logged in
        main_page_response = session.get(main_url, timeout=10)
        debug_info.append(f"Main page final URL: {main_page_response.url}")
        
        if 'login.php' not in main_page_response.url:
            debug_info.append("Already logged in - main page accessible without redirect to login")
            return jsonify({
                'success': True,
                'message': 'Already logged into MAM (main page accessible)',
                'redirect_url': main_page_response.url,
                'debug_info': debug_info
            })
        
        # If we reach here, we need to login - parse the login page for input fields
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for form element first
        login_form = soup.find('form')
        
        # If no form found, look directly for input fields (MAM might not use standard form structure)
        if not login_form:
            debug_info.append("No <form> element found, looking for input fields directly")
            # Look for any input fields on the page
            all_inputs = soup.find_all('input')
            if not all_inputs:
                debug_info.append("No input fields found on page")
                # Show page snippet for debugging
                page_snippet = response.text[:1000] + "..." if len(response.text) > 1000 else response.text
                debug_info.append(f"Page content: {page_snippet}")
                return jsonify({
                    'success': False,
                    'message': 'Could not find any input fields on MAM login page',
                    'debug_info': debug_info
                })
            debug_info.append(f"Found {len(all_inputs)} input fields without form wrapper")
        
        # Get all input fields (either from form or entire page)
        if login_form:
            debug_info.append(f"Form found with action: {login_form.get('action', 'No action')}")
            all_inputs = login_form.find_all('input')
            form_action = login_form.get('action', '/takelogin.php')
        else:
            all_inputs = soup.find_all('input')
            # Default action for MAM
            form_action = '/takelogin.php'
            
        input_info = []
        for inp in all_inputs:
            input_info.append(f"{inp.get('name', 'unnamed')}({inp.get('type', 'text')})")
        debug_info.append(f"Input fields found: {', '.join(input_info)}")
        
        # Prepare login data - try multiple common field names
        login_data = {}
        
        # Find username field - look in all_inputs we found
        username_field = None
        for field_name in ['email', 'username', 'user', 'login']:  # email first since MAM uses email
            for inp in all_inputs:
                if inp.get('name') == field_name:
                    username_field = field_name
                    break
            if username_field:
                break
        
        # Find password field  
        password_field = None
        for field_name in ['password', 'pass', 'pwd']:
            for inp in all_inputs:
                if inp.get('name') == field_name:
                    password_field = field_name
                    break
            if password_field:
                break
                
        if username_field and password_field:
            login_data[username_field] = username
            login_data[password_field] = password
            debug_info.append(f"Using fields: {username_field}, {password_field}")
        else:
            debug_info.append("Could not identify username/password fields")
            return jsonify({
                'success': False,
                'message': 'Could not identify login form fields',
                'debug_info': debug_info
            })
        
        # Add any hidden form fields
        for inp in all_inputs:
            if inp.get('type') == 'hidden' and inp.get('name') and inp.get('value'):
                login_data[inp['name']] = inp['value']
                debug_info.append(f"Added hidden field: {inp['name']}")
        
        # Submit login form using the form_action we determined earlier
        if not form_action.startswith('http'):
            form_action = mam_url.rstrip('/') + '/' + form_action.lstrip('/')
        
        debug_info.append(f"Submitting to: {form_action}")
        debug_info.append(f"Login data keys: {list(login_data.keys())}")
        
        # Check that we have cookies before submitting
        cookies_info = []
        for cookie in session.cookies:
            cookies_info.append(f"{cookie.name}")
        debug_info.append(f"Cookies before login: {', '.join(cookies_info) if cookies_info else 'None'}")
        
        # Add another small delay
        time.sleep(1)
        
        # Set proper headers for form submission
        form_headers = {
            'Referer': login_url,
            'Origin': mam_url.rstrip('/'),
            'Content-Type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        }
        
        login_response = session.post(form_action, data=login_data, headers=form_headers, timeout=10, allow_redirects=True)
        
        debug_info.append(f"Login response status: {login_response.status_code}")
        debug_info.append(f"Final redirect URL: {login_response.url}")
        
        if login_response.status_code != 200:
            return jsonify({
                'success': False,
                'message': f'Login request failed. Status: {login_response.status_code}',
                'debug_info': debug_info
            })
        
        # Check if login was successful - look for common failure indicators
        response_text_lower = login_response.text.lower()
        
        # Check for specific error messages first
        if 'cookies are not really enabled' in response_text_lower:
            error_msg = "Cookie error detected. MAM thinks cookies are disabled."
            debug_info.append("Specific error: Cookies not enabled")
            return jsonify({
                'success': False,
                'message': error_msg,
                'debug_info': debug_info
            })
        
        # Common failure indicators
        failure_indicators = [
            'login.php' in login_response.url,
            'invalid' in response_text_lower,
            'incorrect' in response_text_lower,
            'error' in response_text_lower and 'login' in response_text_lower,
            'username' in response_text_lower and 'password' in response_text_lower and 'form' in response_text_lower
        ]
        
        debug_info.append(f"Failure indicators: {sum(failure_indicators)} found")
        
        if any(failure_indicators):
            # Look for specific error messages
            error_msg = "Login failed. Please check your username and password."
            if 'invalid' in response_text_lower:
                error_msg += " (Invalid credentials)"
            elif 'banned' in response_text_lower or 'disabled' in response_text_lower:
                error_msg += " (Account may be banned/disabled)"
            elif 'robot' in response_text_lower or 'bot' in response_text_lower:
                error_msg += " (Detected as automated - need better browser simulation)"
            
            return jsonify({
                'success': False,
                'message': error_msg,
                'debug_info': debug_info
            })
        
        debug_info.append("Login appears successful")
        return jsonify({
            'success': True,
            'message': 'Successfully logged into MAM',
            'redirect_url': login_response.url,
            'debug_info': debug_info
        })
        
    except Exception as e:
        print(f"MAM login error: {e}")
        debug_info.append(f"Exception: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Login error: {str(e)}',
            'debug_info': debug_info
        })

@app.route('/api/view_mam_page', methods=['GET'])
def api_view_mam_page():
    """View the current MAM page content for debugging"""
    settings = load_settings()
    mam_url = settings.get('mam_url', 'https://www.myanonamouse.net/')
    
    try:
        session = get_mam_session()
        
        # Get the current page (either login or main page)
        page_url = request.args.get('url', mam_url)
        if not page_url.startswith('http'):
            page_url = mam_url.rstrip('/') + '/' + page_url.lstrip('/')
            
        response = session.get(page_url, timeout=10)
        
        return jsonify({
            'success': True,
            'url': response.url,
            'status_code': response.status_code,
            'content': response.text[:2000],  # First 2000 chars
            'content_length': len(response.text),
            'cookies': [{'name': c.name, 'value': c.value[:50]} for c in session.cookies]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
