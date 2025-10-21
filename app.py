from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
import json
import requests
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
import atexit
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SETTINGS_FILE = os.path.join('/app/data', 'settings.json')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This goes to container logs
    ]
)
logger = logging.getLogger(__name__)

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
    # Update log level when settings are saved
    update_log_level()

def update_log_level():
    """Update logging level based on settings"""
    settings = load_settings()
    log_level = settings.get('loglevel', 'Info')
    
    if log_level.lower() == 'debug':
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Log level set to DEBUG")
    else:
        logger.setLevel(logging.INFO)
        logging.getLogger().setLevel(logging.INFO)
        logger.info("Log level set to INFO")

def log_info(message):
    """Log info level message"""
    logger.info(message)

def log_debug(message):
    """Log debug level message"""
    logger.debug(message)

app = Flask(__name__)

# Initialize logging level from settings
update_log_level()
log_info("MAMRenewARR application starting up")

# Global browser instance for session management
global_driver = None

def cleanup_global_driver():
    """Cleanup global browser instance on app shutdown"""
    global global_driver
    if global_driver:
        try:
            global_driver.quit()
            log_info("Global browser instance closed")
        except Exception as e:
            log_info(f"Error closing global browser: {e}")
        finally:
            global_driver = None

# Register cleanup function
atexit.register(cleanup_global_driver)

def get_or_create_global_driver():
    """Get existing global driver or create a new one"""
    global global_driver
    
    # Check if driver exists and is still alive
    if global_driver:
        try:
            # Test if driver is still alive by getting current URL
            _ = global_driver.current_url
            log_debug("Reusing existing global browser instance")
            return global_driver
        except Exception as e:
            log_info(f"Global driver is dead, creating new one. Error: {e}")
            global_driver = None
    
    # Create new driver
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        global_driver = webdriver.Chrome(service=service, options=chrome_options)
        log_info("Created new global browser instance")
        return global_driver
        
    except Exception as e:
        log_info(f"Error creating global driver: {e}")
        return None

def ensure_mam_login(driver, settings):
    """Ensure the driver is logged into MAM"""
    mam_url = settings.get('mam_url', 'https://www.myanonamouse.net/')
    username = settings.get('mam_username', '')
    password = settings.get('mam_password', '')
    
    if not username or not password:
        raise Exception('MAM credentials not configured')
    
    try:
        # Check current URL to see if we need to login
        current_url = driver.current_url
        if 'myanonamouse.net' not in current_url:
            # Navigate to main page first
            driver.get(mam_url.rstrip('/'))
            time.sleep(2)
        
        # Check if we're already logged in
        if 'login.php' not in driver.current_url:
            return True  # Already logged in
        
        # Need to login
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import NoSuchElementException
        
        login_url = mam_url.rstrip('/') + '/login.php'
        driver.get(login_url)
        time.sleep(2)
        
        # Find and fill login form
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        
        email_field.clear()
        email_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        
        # Try to check remember me
        try:
            remember_checkbox = driver.find_element(By.NAME, "rememberMe")
            if not remember_checkbox.is_selected():
                remember_checkbox.click()
        except NoSuchElementException:
            pass
        
        # Submit form
        login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        login_button.click()
        time.sleep(3)
        
        # Check if login successful
        if 'login.php' not in driver.current_url:
            return True
        else:
            raise Exception('Login failed - still on login page')
            
    except Exception as e:
        raise Exception(f'Login error: {str(e)}')

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
    """Login to MyAnonamouse using global Selenium driver"""
    log_info("MAM login attempt started")
    settings = load_settings()
    debug_info = []
    
    # Get credentials from settings
    mam_url = settings.get('mam_url', 'https://www.myanonamouse.net/')
    username = settings.get('mam_username', '')
    password = settings.get('mam_password', '')
    
    log_debug(f"MAM URL: {mam_url}")
    log_debug(f"Username provided: {'Yes' if username else 'No'}")
    log_debug(f"Password provided: {'Yes' if password else 'No'}")
    
    debug_info.append(f"MAM URL: {mam_url}")
    debug_info.append(f"Using global Selenium driver")
    debug_info.append(f"Username provided: {'Yes' if username else 'No'}")
    debug_info.append(f"Password provided: {'Yes' if password else 'No'}")
    
    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'MAM username or password not configured. Please check your settings.',
            'debug_info': debug_info
        })
    
    try:
        driver = get_or_create_global_driver()
        if not driver:
            return jsonify({
                'success': False,
                'message': 'Could not create browser instance',
                'debug_info': debug_info
            })
            
        debug_info.append("Using global browser instance")
        
        # Use the ensure_mam_login helper function
        try:
            ensure_mam_login(driver, settings)
            debug_info.append("Login successful")
            log_info("MAM login successful")
            
            return jsonify({
                'success': True,
                'message': 'Successfully logged into MAM',
                'redirect_url': driver.current_url,
                'debug_info': debug_info
            })
            
        except Exception as e:
            debug_info.append(f"Login failed: {str(e)}")
            log_info(f"MAM login failed: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Login failed: {str(e)}',
                'debug_info': debug_info
            })
            
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
    """Return current state of global Selenium driver (for popup window)"""
    settings = load_settings()
    mam_url = settings.get('mam_url', 'https://www.myanonamouse.net/')
    debug_info = []
    
    try:
        driver = get_or_create_global_driver()
        if not driver:
            return jsonify({
                'success': False,
                'error': 'Could not create browser instance',
                'debug_info': debug_info
            })
            
        debug_info.append("Using global browser instance")
        
        # Don't navigate, just get current state
        current_url = driver.current_url
        page_title = driver.title
        
        debug_info.append(f"Current browser URL: {current_url}")
        debug_info.append(f"Current browser title: {page_title}")
        
        # Check if we're logged in based on URL
        logged_in = 'login.php' not in current_url
        if logged_in:
            debug_info.append("User appears to be logged in")
        else:
            debug_info.append("User appears to be NOT logged in")
        
        return jsonify({
            'success': True,
            'url': current_url,  # Return actual current URL of global browser
            'title': page_title,
            'logged_in': logged_in,
            'debug_info': debug_info
        })
            
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

@app.route('/api/view_sessions', methods=['POST'])
def api_view_sessions():
    """Navigate global browser to MAM security/sessions page"""
    log_info("View Sessions request started")
    settings = load_settings()
    security_page_url = settings.get('security_page', 'https://www.myanonamouse.net/preferences/index.php?view=security')
    log_debug(f"Security page URL: {security_page_url}")
    debug_info = []
    
    try:
        driver = get_or_create_global_driver()
        if not driver:
            return jsonify({
                'success': False,
                'message': 'Could not create browser instance',
                'debug_info': debug_info
            })
            
        debug_info.append("Using global browser instance")
        
        # Ensure we're logged into MAM
        try:
            ensure_mam_login(driver, settings)
            debug_info.append("Login ensured")
        except Exception as e:
            debug_info.append(f"Login failed: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Login failed: {str(e)}',
                'debug_info': debug_info
            })
        
        # Navigate to security page
        debug_info.append(f"Navigating global browser to security page: {security_page_url}")
        log_info(f"Navigating global browser to security page")
        driver.get(security_page_url)
        time.sleep(3)
        
        # Verify we're on the right page
        current_url = driver.current_url
        page_title = driver.title
        debug_info.append(f"Navigated to: {current_url}")
        debug_info.append(f"Page title: {page_title}")
        log_debug(f"Navigated to: {current_url}")
        log_debug(f"Page title: {page_title}")
        
        # Quick check for sessions table to confirm we're on the right page
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import NoSuchElementException
        
        try:
            table = driver.find_element(By.CLASS_NAME, "sessions")
            rows = table.find_elements(By.TAG_NAME, "tr")
            session_count = len(rows) - 1  # Subtract header row
            debug_info.append(f"Found sessions table with {session_count} sessions")
            
            return jsonify({
                'success': True,
                'message': f'Successfully navigated to security page - found {session_count} sessions',
                'current_url': current_url,
                'session_count': session_count,
                'debug_info': debug_info
            })
            
        except NoSuchElementException:
            debug_info.append("Sessions table not found on page")
            return jsonify({
                'success': True,  # Still successful navigation
                'message': 'Navigated to security page (sessions table not found)',
                'current_url': current_url,
                'debug_info': debug_info
            })
            
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'Selenium not available.',
            'debug_info': debug_info
        })
    except Exception as e:
        debug_info.append(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'debug_info': debug_info
        })

@app.route('/api/delete_old_sessions', methods=['POST'])
def api_delete_old_sessions():
    """Delete all old MAM sessions except the newest one"""
    log_info("Delete Old Sessions request started")
    settings = load_settings()
    security_page_url = settings.get('security_page', 'https://www.myanonamouse.net/preferences/index.php?view=security')
    log_debug(f"Security page URL: {security_page_url}")
    debug_info = []
    
    try:
        driver = get_or_create_global_driver()
        if not driver:
            return jsonify({
                'success': False,
                'message': 'Could not create browser instance',
                'debug_info': debug_info
            })
            
        debug_info.append("Using global browser instance")
        
        # Ensure we're logged into MAM
        try:
            ensure_mam_login(driver, settings)
            debug_info.append("Login ensured")
        except Exception as e:
            debug_info.append(f"Login failed: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Login failed: {str(e)}',
                'debug_info': debug_info
            })
        
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import NoSuchElementException
        
        deleted_count = 0
        total_iterations = 0
        max_iterations = 20  # Safety limit
        
        while total_iterations < max_iterations:
            # Navigate to security page
            debug_info.append(f"Iteration {total_iterations + 1}: Loading security page")
            driver.get(security_page_url)
            time.sleep(3)
            
            # Count sessions at start of iteration
            try:
                initial_table = driver.find_element(By.CLASS_NAME, "sessions")
                initial_rows = initial_table.find_elements(By.TAG_NAME, "tr")
                initial_session_count = len(initial_rows) - 1  # Subtract header
                debug_info.append(f"Iteration {total_iterations + 1}: Found {initial_session_count} sessions at start")
                log_debug(f"Iteration {total_iterations + 1}: Starting with {initial_session_count} sessions")
            except Exception as e:
                debug_info.append(f"Could not count initial sessions: {e}")
                initial_session_count = 0
            
            try:
                # Find the sessions table
                table = driver.find_element(By.CLASS_NAME, "sessions")
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                if len(rows) <= 2:  # Header + 1 session = only newest left
                    debug_info.append("Only one session remaining - stopping")
                    break
                
                # Parse sessions with dates
                sessions = []
                debug_info.append(f"Processing {len(rows)-1} session rows (excluding header)")
                log_debug(f"Processing {len(rows)-1} session rows for deletion analysis")
                
                for i, row in enumerate(rows[1:]):  # Skip header
                    cells = row.find_elements(By.TAG_NAME, "td")
                    debug_info.append(f"Row {i+1}: Found {len(cells)} cells")
                    
                    if len(cells) >= 6:
                        created_date_text = cells[0].text.strip()
                        debug_info.append(f"Row {i+1}: Created date text: '{created_date_text}'")
                        
                        try:
                            # Parse date in format: "2025-10-21 09:17:50"
                            created_date = datetime.strptime(created_date_text, "%Y-%m-%d %H:%M:%S")
                            debug_info.append(f"Row {i+1}: Successfully parsed date: {created_date}")
                            
                            # Look for Remove Session button in last column
                            remove_button = None
                            last_cell = cells[-1]
                            debug_info.append(f"Row {i+1}: Last cell HTML: {last_cell.get_attribute('outerHTML')[:200]}...")
                            
                            # Try multiple selectors for the remove button
                            selectors = [
                                'input[data-secact="rs"]',
                                'input[value="Remove Session"]',
                                '*[data-secact="rs"]'
                            ]
                            
                            for selector in selectors:
                                try:
                                    remove_button = last_cell.find_element(By.CSS_SELECTOR, selector)
                                    debug_info.append(f"Row {i+1}: Found remove button with selector '{selector}'")
                                    break
                                except NoSuchElementException:
                                    debug_info.append(f"Row {i+1}: No button found with selector '{selector}'")
                                    continue
                            
                            sessions.append({
                                'row_index': i,
                                'created_date': created_date,
                                'created_date_text': created_date_text,
                                'remove_button': remove_button,
                                'has_remove_button': remove_button is not None,
                                'row': row
                            })
                            
                        except ValueError as e:
                            debug_info.append(f"Row {i+1}: Could not parse date '{created_date_text}': {e}")
                            continue
                    else:
                        debug_info.append(f"Row {i+1}: Insufficient cells ({len(cells)} < 6), skipping")
                
                if len(sessions) <= 1:
                    debug_info.append("Only one valid session found - stopping")
                    break
                
                # Sort by date to find newest (last)
                sessions.sort(key=lambda x: x['created_date'])
                newest_session = sessions[-1]
                
                debug_info.append(f"Found {len(sessions)} sessions. Newest: {newest_session['created_date_text']}")
                
                # Find oldest session with Remove button
                removed_this_iteration = False
                for session in sessions[:-1]:  # All except newest
                    if session['remove_button']:
                        debug_info.append(f"Removing session from {session['created_date_text']}")
                        log_info(f"Attempting to remove session from {session['created_date_text']}")
                        
                        try:
                            # Get current page info before click
                            pre_click_url = driver.current_url
                            debug_info.append(f"Pre-click URL: {pre_click_url}")
                            
                            # Try multiple click methods
                            debug_info.append(f"Clicking remove button for session {session['created_date_text']}")
                            
                            # Method 1: Regular click
                            session['remove_button'].click()
                            time.sleep(0.5)
                            
                            # Method 2: Try JavaScript click as backup
                            try:
                                driver.execute_script("arguments[0].click();", session['remove_button'])
                                debug_info.append("Also tried JavaScript click")
                            except Exception as js_error:
                                debug_info.append(f"JavaScript click failed: {js_error}")
                            
                            # Wait and check for any page changes or alerts
                            time.sleep(1)
                            
                            # Check if there are any alerts/confirmations
                            try:
                                alert = driver.switch_to.alert
                                alert_text = alert.text
                                debug_info.append(f"Alert detected: {alert_text}")
                                log_info(f"Alert after remove button click: {alert_text}")
                                alert.accept()  # Accept the alert
                                debug_info.append("Alert accepted")
                                time.sleep(1)
                            except:
                                debug_info.append("No alert detected")
                            
                            # Check if URL changed or page reloaded
                            post_click_url = driver.current_url
                            debug_info.append(f"Post-click URL: {post_click_url}")
                            
                            if post_click_url != pre_click_url:
                                debug_info.append("Page URL changed - possible redirect")
                            else:
                                debug_info.append("Page URL unchanged - checking for AJAX response")
                            
                            # Wait longer for any AJAX operations
                            time.sleep(2)
                            
                            # Check if the button still exists (it might disappear if session removed)
                            button_still_exists = True
                            try:
                                # Try to find the button again
                                last_cell = cells[-1]
                                test_button = last_cell.find_element(By.CSS_SELECTOR, 'input[data-secact="rs"]')
                                debug_info.append("Remove button still exists after click")
                            except:
                                button_still_exists = False
                                debug_info.append("Remove button no longer exists after click")
                            
                            deleted_count += 1
                            removed_this_iteration = True
                            debug_info.append(f"Completed removal attempt {deleted_count} for session {session['created_date_text']}")
                            log_info(f"Completed removal attempt {deleted_count} (from {session['created_date_text']}) - button_exists_after: {button_still_exists}")
                            break  # Remove one at a time
                            
                        except Exception as e:
                            debug_info.append(f"Error clicking remove button: {e}")
                            log_info(f"Error clicking remove button for session {session['created_date_text']}: {e}")
                            continue
                
                # Verify if session count actually changed
                if removed_this_iteration:
                    # Reload page and check session count
                    time.sleep(1)
                    driver.get(security_page_url)
                    time.sleep(2)
                    
                    try:
                        final_table = driver.find_element(By.CLASS_NAME, "sessions")
                        final_rows = final_table.find_elements(By.TAG_NAME, "tr")
                        final_session_count = len(final_rows) - 1
                        
                        debug_info.append(f"Session count: {initial_session_count} -> {final_session_count}")
                        log_info(f"Iteration {total_iterations + 1}: Session count changed from {initial_session_count} to {final_session_count}")
                        
                        if final_session_count >= initial_session_count:
                            debug_info.append("WARNING: Session count did not decrease - removal may have failed")
                            log_info(f"WARNING: Session removal appeared to fail - count unchanged ({initial_session_count} -> {final_session_count})")
                    except Exception as e:
                        debug_info.append(f"Could not verify final session count: {e}")
                
                if not removed_this_iteration:
                    debug_info.append("No more sessions to remove")
                    break
                    
            except NoSuchElementException:
                debug_info.append("Sessions table not found")
                break
            
            total_iterations += 1
        
        if total_iterations >= max_iterations:
            debug_info.append(f"Reached maximum iterations ({max_iterations})")
        
        final_message = f'Successfully removed {deleted_count} old sessions'
        log_info(f"Delete Old Sessions completed: {final_message} in {total_iterations} iterations")
        
        return jsonify({
            'success': True,
            'message': final_message,
            'deleted_count': deleted_count,
            'iterations': total_iterations,
            'debug_info': debug_info
        })
            
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'Selenium not available.',
            'debug_info': debug_info
        })
    except Exception as e:
        debug_info.append(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Delete sessions error: {str(e)}',
            'debug_info': debug_info
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
