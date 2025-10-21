from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
import os
import subprocess
import re
import requests
import time
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
        
        # More realistic browser headers with JavaScript support indicated
        mam_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',  # Disable compression to avoid decoding issues
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
    """Login to MyAnonamouse using Selenium for JavaScript support"""
    settings = load_settings()
    debug_info = []
    
    # Get credentials from settings
    mam_url = settings.get('mam_url', 'https://www.myanonamouse.net/')
    username = settings.get('mam_username', '')
    password = settings.get('mam_password', '')
    
    debug_info.append(f"MAM URL: {mam_url}")
    debug_info.append(f"Using Selenium for JavaScript support")
    debug_info.append(f"Username provided: {'Yes' if username else 'No'}")
    debug_info.append(f"Password provided: {'Yes' if password else 'No'}")
    
    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'MAM username or password not configured. Please check your settings.',
            'debug_info': debug_info
        })
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.common.exceptions import NoSuchElementException
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Setup Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        debug_info.append("Installing/updating ChromeDriver automatically")
        # Use ChromeDriverManager to automatically download matching version
        service = Service(ChromeDriverManager().install())
        
        debug_info.append("Starting Chrome browser with auto-managed driver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            # Navigate to MAM login page
            login_url = mam_url.rstrip('/') + '/login.php'
            debug_info.append(f"Navigating to: {login_url}")
            driver.get(login_url)
            
            # Wait for page to load
            time.sleep(2)
            debug_info.append(f"Current URL: {driver.current_url}")
            
            # Check if already logged in
            if 'login.php' not in driver.current_url:
                debug_info.append("Already logged in - redirected away from login page")
                return jsonify({
                    'success': True,
                    'message': 'Already logged into MAM',
                    'redirect_url': driver.current_url,
                    'debug_info': debug_info
                })
            
            # Find email and password fields
            try:
                email_field = driver.find_element(By.NAME, "email")
                password_field = driver.find_element(By.NAME, "password")
                debug_info.append("Found email and password fields")
                
                # Enter credentials
                email_field.clear()
                email_field.send_keys(username)
                password_field.clear()
                password_field.send_keys(password)
                debug_info.append("Entered credentials")
                
                # Find and click remember me checkbox
                try:
                    remember_checkbox = driver.find_element(By.NAME, "rememberMe")
                    if not remember_checkbox.is_selected():
                        remember_checkbox.click()
                        debug_info.append("Checked remember me")
                except NoSuchElementException:
                    debug_info.append("Remember me checkbox not found")
                
                # Find and click login button
                login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                debug_info.append(f"Found login button: {login_button.get_attribute('value')}")
                
                # Click login button
                login_button.click()
                debug_info.append("Clicked login button")
                
                # Wait for redirect or error
                time.sleep(3)
                final_url = driver.current_url
                debug_info.append(f"Final URL: {final_url}")
                
                # Check if login was successful
                if 'login.php' not in final_url:
                    debug_info.append("Login successful - redirected away from login page")
                    
                    # Get cookies for potential future use
                    cookies = driver.get_cookies()
                    debug_info.append(f"Got {len(cookies)} cookies")
                    
                    return jsonify({
                        'success': True,
                        'message': 'Successfully logged into MAM',
                        'redirect_url': final_url,
                        'debug_info': debug_info
                    })
                else:
                    # Check for error messages
                    page_source = driver.page_source
                    if 'cookies are not really enabled' in page_source:
                        error_msg = "Cookie error detected (even with Selenium)"
                    elif 'Login failed' in page_source or 'login failed' in page_source:
                        error_msg = "Login failed - check credentials"
                    else:
                        error_msg = "Login failed - still on login page"
                    
                    debug_info.append(f"Login failed: {error_msg}")
                    # Add page snippet for debugging
                    debug_info.append(f"Page contains: {page_source[:500]}...")
                    
                    return jsonify({
                        'success': False,
                        'message': error_msg,
                        'debug_info': debug_info
                    })
                    
            except NoSuchElementException as e:
                debug_info.append(f"Could not find form elements: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Could not find login form elements',
                    'debug_info': debug_info
                })
                
        finally:
            driver.quit()
            debug_info.append("Closed browser")
            
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'Selenium not available. Install selenium and chrome driver.',
            'debug_info': debug_info
        })
    except Exception as e:
        debug_info.append(f"Selenium error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Selenium login error: {str(e)}',
            'debug_info': debug_info
        })

@app.route('/api/view_mam_page', methods=['GET'])
def api_view_mam_page():
    """View MAM page using Selenium for proper JavaScript rendering"""
    settings = load_settings()
    mam_url = settings.get('mam_url', 'https://www.myanonamouse.net/')
    debug_info = []
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Setup Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        debug_info.append("Starting Chrome browser")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            # Get the requested page URL
            page_url = request.args.get('url', mam_url)
            if not page_url.startswith('http'):
                page_url = mam_url.rstrip('/') + '/' + page_url.lstrip('/')
                
            debug_info.append(f"Navigating to: {page_url}")
            driver.get(page_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Get page info
            current_url = driver.current_url
            page_title = driver.title
            page_source = driver.page_source
            
            debug_info.append(f"Page loaded. Title: {page_title}")
            debug_info.append(f"Current URL: {current_url}")
            
            # Check if we're logged in based on URL and content
            logged_in = 'login.php' not in current_url
            if logged_in:
                debug_info.append("User appears to be logged in")
            else:
                debug_info.append("User appears to be NOT logged in")
            
            return jsonify({
                'success': True,
                'url': current_url,
                'title': page_title,
                'content': page_source[:5000],  # First 5000 chars for inspection
                'content_length': len(page_source),
                'logged_in': logged_in,
                'debug_info': debug_info
            })
            
        finally:
            driver.quit()
            debug_info.append("Closed browser")
            
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Selenium not available. Install selenium and chrome driver.',
            'debug_info': debug_info
        })
    except Exception as e:
        debug_info.append(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'debug_info': debug_info
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
