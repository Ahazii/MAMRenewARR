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
from logging.handlers import RotatingFileHandler
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SETTINGS_FILE = os.path.join('/app/data', 'settings.json')
LOG_FILE = os.path.join('/app/data', 'mamrenewarr.log')

# Ensure data directory exists
os.makedirs('/app/data', exist_ok=True)

# Configure logging with both console and file handlers
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler (for Docker logs)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# File handler (rotating, keeps last 5 files of 10MB each)
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Add both handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Also configure root logger for other libraries
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)
logging.getLogger().addHandler(file_handler)

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
    """Update logging level based on settings for both console and file handlers"""
    settings = load_settings()
    log_level = settings.get('loglevel', 'Info')
    
    if log_level.lower() == 'debug':
        new_level = logging.DEBUG
        logger.setLevel(new_level)
        logging.getLogger().setLevel(new_level)
        
        # Update both console and file handlers
        for handler in logger.handlers:
            handler.setLevel(new_level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(new_level)
        
        logger.debug("Log level set to DEBUG (both console and file)")
    else:
        new_level = logging.INFO
        logger.setLevel(new_level)
        logging.getLogger().setLevel(new_level)
        
        # Update both console and file handlers
        for handler in logger.handlers:
            handler.setLevel(new_level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(new_level)
        
        logger.info("Log level set to INFO (both console and file)")

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
                            
                            # Detailed button analysis before clicking
                            button = session['remove_button']
                            debug_info.append(f"Button details: tag={button.tag_name}, value='{button.get_attribute('value')}', data-secact='{button.get_attribute('data-secact')}'")
                            debug_info.append(f"Button enabled: {button.is_enabled()}, displayed: {button.is_displayed()}, clickable: {button.is_enabled() and button.is_displayed()}")
                            debug_info.append(f"Button location: {button.location}, size: {button.size}")
                            debug_info.append(f"Button HTML: {button.get_attribute('outerHTML')[:200]}...")
                            
                            # Try scrolling to button first
                            try:
                                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.5)
                                debug_info.append("Scrolled button into view")
                            except Exception as scroll_error:
                                debug_info.append(f"Scroll error: {scroll_error}")
                            
                            debug_info.append(f"Attempting to click remove button for session {session['created_date_text']}")
                            
                            # Method 1: Regular click
                            click_successful = False
                            try:
                                button.click()
                                debug_info.append("Regular click executed")
                                click_successful = True
                            except Exception as click_error:
                                debug_info.append(f"Regular click failed: {click_error}")
                            
                            time.sleep(0.5)
                            
                            # Method 2: JavaScript click as backup
                            try:
                                driver.execute_script("arguments[0].click();", button)
                                debug_info.append("JavaScript click executed")
                                click_successful = True
                            except Exception as js_error:
                                debug_info.append(f"JavaScript click failed: {js_error}")
                            
                            # Method 3: Try ActionChains click
                            try:
                                from selenium.webdriver.common.action_chains import ActionChains
                                actions = ActionChains(driver)
                                actions.move_to_element(button).click().perform()
                                debug_info.append("ActionChains click executed")
                                click_successful = True
                            except Exception as action_error:
                                debug_info.append(f"ActionChains click failed: {action_error}")
                            
                            if not click_successful:
                                debug_info.append("ERROR: All click methods failed!")
                                log_info(f"All click methods failed for session {session['created_date_text']}")
                                continue
                            
                            # Wait and check for different types of popups/dialogs
                            confirmation_handled = False
                            max_wait_attempts = 5
                            
                            for wait_attempt in range(max_wait_attempts):
                                time.sleep(0.5)
                                
                                # Method 1: Check for browser alert
                                try:
                                    alert = driver.switch_to.alert
                                    alert_text = alert.text
                                    debug_info.append(f"Browser alert detected on attempt {wait_attempt + 1}: '{alert_text}'")
                                    log_info(f"Browser alert for session removal: '{alert_text}'")
                                    
                                    # Click "OK" to confirm removal
                                    alert.accept()
                                    debug_info.append("Clicked OK on browser alert")
                                    log_info("Confirmed session removal by clicking OK on alert")
                                    confirmation_handled = True
                                    time.sleep(3)
                                    break
                                except:
                                    pass  # No browser alert
                                
                                # Method 2: Check for modal dialogs or confirmation elements
                                try:
                                    # Look for common modal/dialog selectors
                                    modal_selectors = [
                                        ".modal", "[role=dialog]", ".dialog", ".popup", 
                                        "#confirm-dialog", ".confirm-popup", ".swal2-container"
                                    ]
                                    
                                    for selector in modal_selectors:
                                        modals = driver.find_elements(By.CSS_SELECTOR, selector)
                                        for modal in modals:
                                            if modal.is_displayed():
                                                debug_info.append(f"Modal dialog detected with selector '{selector}': {modal.get_attribute('outerHTML')[:150]}...")
                                                
                                                # Look for OK/Confirm button in modal
                                                ok_buttons = modal.find_elements(By.CSS_SELECTOR, 
                                                    "button, input[type='button'], input[type='submit']")
                                                
                                                # Filter buttons by text content
                                                confirm_buttons = []
                                                for btn in ok_buttons:
                                                    btn_text = btn.text.upper() if btn.text else ''
                                                    btn_value = (btn.get_attribute('value') or '').upper()
                                                    if any(keyword in btn_text or keyword in btn_value for keyword in ['OK', 'CONFIRM', 'YES']):
                                                        confirm_buttons.append(btn)
                                                
                                                ok_buttons = confirm_buttons
                                                
                                                if ok_buttons:
                                                    ok_buttons[0].click()
                                                    debug_info.append("Clicked OK button in modal dialog")
                                                    confirmation_handled = True
                                                    time.sleep(3)
                                                    break
                                        
                                        if confirmation_handled:
                                            break
                                            
                                except Exception as modal_error:
                                    debug_info.append(f"Modal check error: {modal_error}")
                                
                                if confirmation_handled:
                                    break
                                    
                                # Check if page changed (might indicate successful click without popup)
                                current_page_url = driver.current_url
                                debug_info.append(f"Attempt {wait_attempt + 1}: Current URL: {current_page_url}")
                                
                                if wait_attempt == max_wait_attempts - 1:
                                    debug_info.append(f"No confirmation dialog found after {max_wait_attempts} attempts")
                                    log_info(f"No confirmation dialog appeared after {max_wait_attempts} attempts")
                            
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
                            
                            # Only count as successful deletion if we handled confirmation dialog OR button disappeared
                            session_actually_removed = confirmation_handled or not button_still_exists
                            
                            if session_actually_removed:
                                deleted_count += 1
                                debug_info.append(f"✓ Successfully removed session {session['created_date_text']}")
                                log_info(f"✓ Successfully removed session from {session['created_date_text']} - confirmation_handled: {confirmation_handled}, button_gone: {not button_still_exists}")
                            else:
                                debug_info.append(f"✗ Failed to remove session {session['created_date_text']} - no confirmation dialog handled and button still exists")
                                log_info(f"✗ Failed to remove session from {session['created_date_text']} - no confirmation dialog handled and button still exists")
                            
                            if not confirmation_handled:
                                debug_info.append("WARNING: No confirmation dialog was handled - session likely not removed")
                                log_info("WARNING: Expected confirmation dialog not found - session removal may have failed")
                            
                            removed_this_iteration = session_actually_removed  # Only mark as removed if actually successful
                            debug_info.append(f"Completed removal attempt for session {session['created_date_text']} - actual_success: {session_actually_removed}")
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

def create_session_cookie(cookie_type, ip_address, use_asn, allow_dynamic_seedbox, label):
    """Helper function to create a session cookie"""
    settings = load_settings()
    security_page_url = settings.get('security_page', 'https://www.myanonamouse.net/preferences/index.php?view=security')
    debug_info = []
    
    try:
        driver = get_or_create_global_driver()
        if not driver:
            return {'success': False, 'message': 'Could not create browser instance', 'debug_info': debug_info}
        
        debug_info.append(f"Creating {cookie_type} session cookie")
        
        # Ensure we're logged into MAM
        try:
            ensure_mam_login(driver, settings)
            debug_info.append("Login ensured")
        except Exception as e:
            debug_info.append(f"Login failed: {str(e)}")
            return {'success': False, 'message': f'Login failed: {str(e)}', 'debug_info': debug_info}
        
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import NoSuchElementException
        
        # Navigate to security page
        debug_info.append("Navigating to security page")
        driver.get(security_page_url)
        time.sleep(3)
        
        # Find the "Create session" form at the bottom
        debug_info.append("Looking for Create session form")
        try:
            # Find the row with "Create session" text
            create_session_row = driver.find_element(By.XPATH, "//td[contains(@class, 'row2') and text()='Create session']")
            debug_info.append("Found Create session row")
            
            # Get the form container (should be in same table)
            form_table = create_session_row.find_element(By.XPATH, "./ancestor::table[1]")
            debug_info.append("Found form table")
            
        except NoSuchElementException:
            debug_info.append("Could not find Create session form")
            return {'success': False, 'message': 'Create session form not found', 'debug_info': debug_info}
        
        # Fill in the IP address
        try:
            ip_field = form_table.find_element(By.ID, "iip")
            ip_field.clear()
            ip_field.send_keys(ip_address)
            debug_info.append(f"Entered IP address: {ip_address}")
        except NoSuchElementException:
            debug_info.append("Could not find IP input field")
            return {'success': False, 'message': 'IP input field not found', 'debug_info': debug_info}
        
        # Select ASN or IP radio button
        try:
            if use_asn:
                # Select ASN radio button
                asn_radio = form_table.find_element(By.CSS_SELECTOR, "input[name='asn'][value='yes']")
                asn_radio.click()
                debug_info.append("Selected ASN radio button")
            else:
                # Select IP radio button
                ip_radio = form_table.find_element(By.CSS_SELECTOR, "input[name='asn'][value='no']")
                ip_radio.click()
                debug_info.append("Selected IP radio button")
        except NoSuchElementException:
            debug_info.append("Could not find ASN/IP radio buttons")
            return {'success': False, 'message': 'ASN/IP radio buttons not found', 'debug_info': debug_info}
        
        # Select Dynamic Seedbox radio button
        try:
            if allow_dynamic_seedbox:
                # Select Yes for dynamic seedbox
                dyn_yes_radio = form_table.find_element(By.CSS_SELECTOR, "input[name='dynSeed'][value='yes']")
                dyn_yes_radio.click()
                debug_info.append("Selected Yes for Dynamic Seedbox")
            else:
                # Select No for dynamic seedbox
                dyn_no_radio = form_table.find_element(By.CSS_SELECTOR, "input[name='dynSeed'][value='no']")
                dyn_no_radio.click()
                debug_info.append("Selected No for Dynamic Seedbox")
        except NoSuchElementException:
            debug_info.append("Could not find Dynamic Seedbox radio buttons")
            return {'success': False, 'message': 'Dynamic Seedbox radio buttons not found', 'debug_info': debug_info}
        
        # Fill in the label
        try:
            label_field = form_table.find_element(By.ID, "sLabel")
            label_field.clear()
            label_field.send_keys(label)
            debug_info.append(f"Entered label: {label}")
        except NoSuchElementException:
            debug_info.append("Could not find label field")
            return {'success': False, 'message': 'Label field not found', 'debug_info': debug_info}
        
        # Click submit button
        try:
            submit_button = form_table.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Submit changes!']")
            submit_button.click()
            debug_info.append("Clicked submit button")
        except NoSuchElementException:
            debug_info.append("Could not find submit button")
            return {'success': False, 'message': 'Submit button not found', 'debug_info': debug_info}
        
        # Wait and handle confirmation dialog
        confirmation_handled = False
        max_wait_attempts = 5
        
        for wait_attempt in range(max_wait_attempts):
            time.sleep(0.5)
            
            # Check for browser alert
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                debug_info.append(f"Confirmation alert detected: '{alert_text}'")
                log_info(f"Session creation confirmation alert: '{alert_text}'")
                
                # Click "OK" to confirm
                alert.accept()
                debug_info.append("Confirmed session creation")
                log_info("Confirmed session creation by clicking OK on alert")
                confirmation_handled = True
                time.sleep(3)
                break
            except:
                pass  # No browser alert
            
            # Check for modal dialogs
            try:
                modal_selectors = [
                    ".modal", "[role=dialog]", ".dialog", ".popup", 
                    "#confirm-dialog", ".confirm-popup", ".swal2-container"
                ]
                
                for selector in modal_selectors:
                    modals = driver.find_elements(By.CSS_SELECTOR, selector)
                    for modal in modals:
                        if modal.is_displayed():
                            debug_info.append(f"Modal dialog detected with selector '{selector}'")
                            
                            # Look for OK/Confirm button in modal
                            ok_buttons = modal.find_elements(By.CSS_SELECTOR, 
                                "button, input[type='button'], input[type='submit']")
                            
                            # Filter buttons by text content
                            confirm_buttons = []
                            for btn in ok_buttons:
                                btn_text = btn.text.upper() if btn.text else ''
                                btn_value = (btn.get_attribute('value') or '').upper()
                                if any(keyword in btn_text or keyword in btn_value for keyword in ['OK', 'CONFIRM', 'YES']):
                                    confirm_buttons.append(btn)
                            
                            ok_buttons = confirm_buttons
                            
                            if ok_buttons:
                                ok_buttons[0].click()
                                debug_info.append("Clicked OK button in modal dialog")
                                confirmation_handled = True
                                time.sleep(3)
                                break
                    
                    if confirmation_handled:
                        break
            except Exception as modal_error:
                debug_info.append(f"Modal check error: {modal_error}")
            
            if confirmation_handled:
                break
        
        if not confirmation_handled:
            debug_info.append("WARNING: No confirmation dialog was handled")
            log_info("WARNING: No confirmation dialog found for session creation")
        
        # Wait for page to load and extract cookie
        time.sleep(3)
        
        try:
            # Look for the cookie textarea
            cookie_textarea = driver.find_element(By.XPATH, "//textarea[@cols='100'][@rows='10']")
            cookie_value = cookie_textarea.get_attribute('value')
            debug_info.append(f"Extracted cookie (length: {len(cookie_value)})")
            
            if not cookie_value or len(cookie_value) < 50:
                debug_info.append("Cookie appears to be empty or too short")
                return {'success': False, 'message': 'Cookie extraction failed - empty or invalid cookie', 'debug_info': debug_info}
            
            # Store cookie in settings with timestamp
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            settings = load_settings()
            if cookie_type == 'qBittorrent':
                settings['qbittorrent_session_cookie'] = cookie_value
                settings['qbittorrent_cookie_obtained_time'] = current_time
            elif cookie_type == 'Prowlarr':
                settings['prowlarr_session_cookie'] = cookie_value
                settings['prowlarr_cookie_obtained_time'] = current_time
            
            save_settings(settings)
            debug_info.append(f"Saved {cookie_type} cookie and timestamp ({current_time}) to settings")
            
            # Refresh the page to show the new session
            debug_info.append("Refreshing page to show new session")
            driver.get(security_page_url)
            time.sleep(2)
            
            log_info(f"✓ Successfully created {cookie_type} session cookie")
            
            return {
                'success': True, 
                'message': f'Successfully created {cookie_type} session cookie',
                'cookie': cookie_value[:50] + '...' if len(cookie_value) > 50 else cookie_value,  # Truncated for display
                'debug_info': debug_info
            }
            
        except NoSuchElementException:
            debug_info.append("Could not find cookie textarea")
            return {'success': False, 'message': 'Cookie textarea not found', 'debug_info': debug_info}
        
    except ImportError:
        return {'success': False, 'message': 'Selenium not available.', 'debug_info': debug_info}
    except Exception as e:
        debug_info.append(f"Error: {str(e)}")
        return {'success': False, 'message': f'Session creation error: {str(e)}', 'debug_info': debug_info}

@app.route('/api/logout_mam', methods=['POST'])
def api_logout_mam():
    """Logout from MAM by closing the browser session"""
    log_info("MAM Logout request started")
    
    try:
        global global_driver
        
        if global_driver:
            try:
                # Close the browser
                global_driver.quit()
                log_info("Browser session closed successfully")
                return jsonify({
                    'success': True,
                    'message': 'Successfully logged out from MAM (browser closed)'
                })
            except Exception as e:
                log_info(f"Error closing browser: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error closing browser: {str(e)}'
                })
            finally:
                global_driver = None
        else:
            return jsonify({
                'success': True,
                'message': 'No active browser session to close'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Logout error: {str(e)}'
        })

@app.route('/api/clear_cookies', methods=['POST'])
def api_clear_cookies():
    """Clear stored session cookies by setting them to '0' with current timestamp"""
    log_info("Clear Cookies request started")
    
    try:
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        settings = load_settings()
        
        # Set both cookies to '0' and update timestamps
        settings['qbittorrent_session_cookie'] = '0'
        settings['qbittorrent_cookie_obtained_time'] = current_time
        settings['prowlarr_session_cookie'] = '0'
        settings['prowlarr_cookie_obtained_time'] = current_time
        
        save_settings(settings)
        log_info(f"Cleared both session cookies and set timestamps to: {current_time}")
        
        return jsonify({
            'success': True,
            'message': 'Successfully cleared both session cookies',
            'timestamp': current_time
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error clearing cookies: {str(e)}'
        })

@app.route('/api/create_qbittorrent_cookie', methods=['POST'])
def api_create_qbittorrent_cookie():
    """Create qBittorrent session cookie"""
    log_info("Create qBittorrent Session Cookie request started")
    
    try:
        # Get VPN IP by calling the existing get_ips endpoint
        from flask import current_app
        with current_app.test_client() as client:
            ip_response = client.get('/api/get_ips')
            ip_data = ip_response.get_json()
        
        if not ip_data or ip_data.get('vpn_ip') == 'Not Found':
            return jsonify({
                'success': False,
                'message': 'VPN IP not found. Please click "Get IPs" first to detect the VPN IP address.',
                'debug_info': ['VPN IP detection failed or not run yet']
            })
        
        vpn_ip = ip_data.get('vpn_ip')
        debug_info = [f"Using VPN IP from Get IPs: {vpn_ip}"]
        
        # Create qBittorrent session cookie
        result = create_session_cookie(
            cookie_type='qBittorrent',
            ip_address=vpn_ip,
            use_asn=True,  # Select ASN radio button
            allow_dynamic_seedbox=True,  # Select Yes for dynamic seedbox
            label='qBittorrent'
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating qBittorrent cookie: {str(e)}',
            'debug_info': [str(e)]
        })

@app.route('/api/create_prowlarr_cookie', methods=['POST'])
def api_create_prowlarr_cookie():
    """Create Prowlarr session cookie"""
    log_info("Create Prowlarr Session Cookie request started")
    
    # Get external IP for Prowlarr
    try:
        ext_ip = requests.get('https://api.ipify.org', timeout=10).text.strip()
        
        if not ext_ip:
            return jsonify({
                'success': False,
                'message': 'External IP not found. Please check your internet connection.',
                'debug_info': ['Failed to get external IP']
            })
        
        # Create Prowlarr session cookie
        result = create_session_cookie(
            cookie_type='Prowlarr',
            ip_address=ext_ip,
            use_asn=False,  # Select IP radio button
            allow_dynamic_seedbox=False,  # Select No for dynamic seedbox
            label='Prowlarr'
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating Prowlarr cookie: {str(e)}',
            'debug_info': [str(e)]
        })

# Global variable to track qBittorrent container connection state
qbittorrent_container_connected = False

@app.route('/api/qbittorrent_login', methods=['POST'])
def api_qbittorrent_login():
    """Connect to qBittorrent container console"""
    log_info("qBittorrent Login request started")
    debug_info = []
    
    try:
        import subprocess
        global qbittorrent_container_connected
        
        debug_info.append("Attempting to connect to binhex-qbittorrentvpn container")
        
        # Test if container exists and is running
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=binhex-qbittorrentvpn', '--format', '{{.Names}}']
                , capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                debug_info.append(f"Docker ps command failed: {result.stderr}")
                log_info(f"Docker ps command failed: {result.stderr}")
                return jsonify({
                    'success': False,
                    'message': 'Failed to check Docker container status',
                    'debug_info': debug_info
                })
            
            container_list = result.stdout.strip().split('\n')
            debug_info.append(f"Found containers: {container_list}")
            
            if not any('binhex-qbittorrentvpn' in name for name in container_list if name):
                debug_info.append("binhex-qbittorrentvpn container not found or not running")
                log_info("binhex-qbittorrentvpn container not found or not running")
                return jsonify({
                    'success': False,
                    'message': 'binhex-qbittorrentvpn container not found or not running',
                    'debug_info': debug_info
                })
                
        except subprocess.TimeoutExpired:
            debug_info.append("Docker command timed out")
            return jsonify({
                'success': False,
                'message': 'Docker command timed out',
                'debug_info': debug_info
            })
        except Exception as e:
            debug_info.append(f"Error checking container status: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error checking container status: {str(e)}',
                'debug_info': debug_info
            })
        
        # Test basic command execution in container
        try:
            test_result = subprocess.run(
                ['docker', 'exec', 'binhex-qbittorrentvpn', 'echo', 'test-connection'],
                capture_output=True, text=True, timeout=15
            )
            
            if test_result.returncode == 0:
                qbittorrent_container_connected = True
                debug_info.append("Successfully connected to container")
                debug_info.append(f"Test command output: {test_result.stdout.strip()}")
                log_info("Successfully connected to binhex-qbittorrentvpn container")
                
                return jsonify({
                    'success': True,
                    'message': 'Successfully connected to qBittorrent container console',
                    'debug_info': debug_info
                })
            else:
                debug_info.append(f"Test command failed: {test_result.stderr}")
                log_info(f"Container connection test failed: {test_result.stderr}")
                return jsonify({
                    'success': False,
                    'message': f'Container connection test failed: {test_result.stderr}',
                    'debug_info': debug_info
                })
                
        except subprocess.TimeoutExpired:
            debug_info.append("Container connection test timed out")
            return jsonify({
                'success': False,
                'message': 'Container connection test timed out',
                'debug_info': debug_info
            })
            
    except Exception as e:
        debug_info.append(f"Unexpected error: {str(e)}")
        log_info(f"qBittorrent login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Connection error: {str(e)}',
            'debug_info': debug_info
        })

@app.route('/api/qbittorrent_send_cookie', methods=['POST'])
def api_qbittorrent_send_cookie():
    """Send qBittorrent cookie to container using curl command"""
    log_info("qBittorrent Send Cookie request started")
    debug_info = []
    
    try:
        import subprocess
        global qbittorrent_container_connected
        
        # Check if we have a connection
        if not qbittorrent_container_connected:
            debug_info.append("No active container connection - please login first")
            return jsonify({
                'success': False,
                'message': 'No active container connection. Please click "Log into qBittorrent" first.',
                'debug_info': debug_info
            })
        
        # Get qBittorrent cookie from settings
        settings = load_settings()
        qb_cookie = settings.get('qbittorrent_session_cookie')
        
        if not qb_cookie or qb_cookie == '0':
            debug_info.append("No qBittorrent cookie found or cookie is cleared")
            log_info("No qBittorrent cookie found - user needs to create one in Step 2")
            return jsonify({
                'success': False,
                'message': 'No qBittorrent cookie found. Please create a qBittorrent session in Step 2 first.',
                'debug_info': debug_info
            })
        
        debug_info.append(f"Using qBittorrent cookie (length: {len(qb_cookie)} chars)")
        debug_info.append(f"Cookie preview: {qb_cookie[:50]}...")
        log_debug(f"Executing curl command with cookie in binhex-qbittorrentvpn container")
        
        # Build the curl command
        curl_command = [
            'docker', 'exec', 'binhex-qbittorrentvpn',
            'sudo', 'curl', '-c', '/path/docker/persists/mam.cookies',
            '-b', f'mam_id={qb_cookie}',
            'https://t.myanonamouse.net/json/dynamicSeedbox.php'
        ]
        
        debug_info.append("Executing curl command in container...")
        debug_info.append(f"Command: {' '.join(curl_command[:8])}... [cookie hidden]")
        log_info("Executing MAM dynamic seedbox curl command in qBittorrent container")
        
        try:
            result = subprocess.run(
                curl_command,
                capture_output=True, text=True, timeout=30
            )
            
            debug_info.append(f"Command exit code: {result.returncode}")
            debug_info.append(f"Command stdout: {result.stdout}")
            if result.stderr:
                debug_info.append(f"Command stderr: {result.stderr}")
            
            log_debug(f"Curl command completed with exit code: {result.returncode}")
            log_debug(f"Curl response: {result.stdout}")
            
            if result.returncode == 0:
                # Parse the response to check for success
                response_text = result.stdout.strip()
                debug_info.append(f"Full response: {response_text}")
                
                # Extract JSON from response
                json_start = response_text.find('{')
                json_data = None
                if json_start != -1:
                    json_part = response_text[json_start:]
                    # Find the end of JSON
                    json_end = json_part.find('}') + 1
                    if json_end > 0:
                        clean_json = json_part[:json_end]
                        debug_info.append(f"Extracted JSON: {clean_json}")
                        try:
                            json_data = json.loads(clean_json)
                        except json.JSONDecodeError:
                            debug_info.append("Failed to parse JSON response")
                
                # Check for success
                if '{"Success":true' in response_text or (json_data and json_data.get('Success') == True):
                    debug_info.append('SUCCESS: Found {"Success":true in response')
                    log_info("✓ Successfully secured qBittorrent session with MAM")
                    
                    return jsonify({
                        'success': True,
                        'message': 'Successfully secured qBittorrent session with MAM',
                        'response': response_text,
                        'debug_info': debug_info
                    })
                # Check for rate limit message
                elif 'Last change too recent' in response_text or (json_data and json_data.get('msg') == 'Last change too recent'):
                    debug_info.append('RATE LIMIT: MAM reports last change too recent')
                    log_info(f"MAM rate limit hit: {response_text}")
                    return jsonify({
                        'success': False,
                        'message': 'MAM rate limit: Last change too recent. Please wait before trying again.',
                        'response': response_text,
                        'debug_info': debug_info
                    })
                else:
                    debug_info.append('FAILURE: Did not find {"Success":true in response')
                    log_info(f"qBittorrent session setup failed - unexpected response: {response_text}")
                    
                    # Try to extract error message from JSON
                    error_msg = 'Session setup failed - unexpected response from MAM'
                    if json_data and json_data.get('msg'):
                        error_msg = f"MAM error: {json_data.get('msg')}"
                    
                    return jsonify({
                        'success': False,
                        'message': error_msg,
                        'response': response_text,
                        'debug_info': debug_info
                    })
            else:
                debug_info.append(f"Curl command failed with exit code: {result.returncode}")
                log_info(f"Curl command failed: {result.stderr}")
                return jsonify({
                    'success': False,
                    'message': f'Curl command failed: {result.stderr}',
                    'debug_info': debug_info
                })
                
        except subprocess.TimeoutExpired:
            debug_info.append("Curl command timed out after 30 seconds")
            log_info("Curl command timed out")
            return jsonify({
                'success': False,
                'message': 'Curl command timed out after 30 seconds',
                'debug_info': debug_info
            })
            
    except Exception as e:
        debug_info.append(f"Unexpected error: {str(e)}")
        log_info(f"qBittorrent send cookie error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Send cookie error: {str(e)}',
            'debug_info': debug_info
        })

@app.route('/api/qbittorrent_logout', methods=['POST'])
def api_qbittorrent_logout():
    """Disconnect from qBittorrent container console"""
    log_info("qBittorrent Logout request started")
    debug_info = []
    
    try:
        global qbittorrent_container_connected
        
        if qbittorrent_container_connected:
            qbittorrent_container_connected = False
            debug_info.append("Disconnected from container console")
            log_info("Disconnected from binhex-qbittorrentvpn container console")
            
            return jsonify({
                'success': True,
                'message': 'Successfully logged out from qBittorrent container console',
                'debug_info': debug_info
            })
        else:
            debug_info.append("No active container connection to close")
            return jsonify({
                'success': True,
                'message': 'No active container connection to close',
                'debug_info': debug_info
            })
            
    except Exception as e:
        debug_info.append(f"Error during logout: {str(e)}")
        log_info(f"qBittorrent logout error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Logout error: {str(e)}',
            'debug_info': debug_info
        })

@app.route('/api/restart_qbittorrent_container', methods=['POST'])
def api_restart_qbittorrent_container():
    """Restart the binhex-qbittorrentvpn Docker container"""
    log_info("Restart qBittorrent Container request started")
    status_updates = []
    
    try:
        import subprocess
        
        # Get settings
        settings = load_settings()
        container_name = settings.get('qbittorrentvpn_container', 'binhex-qbittorrentvpn')
        qbittorrent_url = settings.get('qbittorrent_url', '')
        restart_delay = int(settings.get('qbittorrent_restart_delay', 120))
        
        log_debug(f"Container name: {container_name}")
        log_debug(f"qBittorrent URL: {qbittorrent_url}")
        log_debug(f"Restart delay: {restart_delay} seconds")
        
        if not qbittorrent_url:
            status_updates.append("qBittorrent URL not configured")
            return jsonify({
                'success': False,
                'message': 'qBittorrent URL not configured. Please set in Config page.',
                'status_updates': status_updates
            })
        
        # Ensure URL has http:// prefix
        if not qbittorrent_url.startswith('http'):
            qbittorrent_url = 'http://' + qbittorrent_url
        
        # Check if container exists
        status_updates.append("Checking if container exists...")
        log_info("Checking if container exists")
        
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                status_updates.append(f"Docker command failed: {result.stderr}")
                log_info(f"Docker ps command failed: {result.stderr}")
                return jsonify({
                    'success': False,
                    'message': 'Failed to check Docker container status',
                    'status_updates': status_updates
                })
            
            container_list = result.stdout.strip().split('\n')
            if not any(container_name in name for name in container_list if name):
                status_updates.append(f"Container '{container_name}' not found")
                log_info(f"Container '{container_name}' not found")
                return jsonify({
                    'success': False,
                    'message': f"Container '{container_name}' not found",
                    'status_updates': status_updates
                })
            
            status_updates.append(f"Found container: {container_name}")
            log_info(f"Found container: {container_name}")
            
        except subprocess.TimeoutExpired:
            status_updates.append("Docker command timed out")
            return jsonify({
                'success': False,
                'message': 'Docker command timed out',
                'status_updates': status_updates
            })
        
        # Restart container
        status_updates.append("Restarting container...")
        log_info(f"Restarting container {container_name}")
        
        try:
            result = subprocess.run(
                ['docker', 'restart', container_name],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                status_updates.append("Container restart command sent")
                log_info("Container restart command successful")
            else:
                status_updates.append(f"Restart command failed: {result.stderr}")
                log_info(f"Restart command failed: {result.stderr}")
                return jsonify({
                    'success': False,
                    'message': f'Restart command failed: {result.stderr}',
                    'status_updates': status_updates
                })
        except subprocess.TimeoutExpired:
            status_updates.append("Restart command timed out")
            return jsonify({
                'success': False,
                'message': 'Restart command timed out',
                'status_updates': status_updates
            })
        
        # Monitor URL to check if container is up
        status_updates.append(f"Monitoring {qbittorrent_url} for up to {restart_delay} seconds...")
        log_info(f"Monitoring {qbittorrent_url} for container availability")
        
        start_time = time.time()
        container_up = False
        
        while time.time() - start_time < restart_delay:
            try:
                response = requests.get(qbittorrent_url, timeout=5)
                if response.status_code in [200, 401, 403]:  # Any of these means it's up
                    container_up = True
                    elapsed = int(time.time() - start_time)
                    status_updates.append(f"Container is UP after {elapsed} seconds")
                    log_info(f"Container became accessible after {elapsed} seconds")
                    break
            except requests.exceptions.RequestException:
                pass  # Not up yet, continue waiting
            
            time.sleep(2)  # Wait 2 seconds between checks
        
        if container_up:
            return jsonify({
                'success': True,
                'message': f'Successfully restarted {container_name}',
                'status_updates': status_updates
            })
        else:
            # Fallback: stop and start
            status_updates.append(f"Container did not come up within {restart_delay} seconds")
            status_updates.append("Attempting fallback: stop then start...")
            log_info("Restart failed, attempting fallback stop/start")
            
            # Stop container
            status_updates.append("Stopping container...")
            log_info(f"Stopping container {container_name}")
            
            try:
                result = subprocess.run(
                    ['docker', 'stop', container_name],
                    capture_output=True, text=True, timeout=60
                )
                
                if result.returncode == 0:
                    status_updates.append("Container stopped")
                    log_info("Container stop command successful")
                else:
                    status_updates.append(f"Stop command failed: {result.stderr}")
                    log_info(f"Stop command failed: {result.stderr}")
                    return jsonify({
                        'success': False,
                        'message': f'Stop command failed: {result.stderr}',
                        'status_updates': status_updates
                    })
            except subprocess.TimeoutExpired:
                status_updates.append("Stop command timed out")
                return jsonify({
                    'success': False,
                    'message': 'Stop command timed out',
                    'status_updates': status_updates
                })
            
            # Wait for restart_delay
            status_updates.append(f"Waiting {restart_delay} seconds...")
            log_info(f"Waiting {restart_delay} seconds before starting container")
            time.sleep(restart_delay)
            
            # Start container
            status_updates.append("Starting container...")
            log_info(f"Starting container {container_name}")
            
            try:
                result = subprocess.run(
                    ['docker', 'start', container_name],
                    capture_output=True, text=True, timeout=30
                )
                
                if result.returncode == 0:
                    status_updates.append("Container start command sent")
                    log_info("Container start command successful")
                else:
                    status_updates.append(f"Start command failed: {result.stderr}")
                    log_info(f"Start command failed: {result.stderr}")
                    return jsonify({
                        'success': False,
                        'message': f'Start command failed: {result.stderr}',
                        'status_updates': status_updates
                    })
            except subprocess.TimeoutExpired:
                status_updates.append("Start command timed out")
                return jsonify({
                    'success': False,
                    'message': 'Start command timed out',
                    'status_updates': status_updates
                })
            
            # Monitor again
            status_updates.append(f"Monitoring {qbittorrent_url} for up to {restart_delay} seconds...")
            log_info(f"Monitoring {qbittorrent_url} again after manual start")
            
            start_time = time.time()
            container_up = False
            
            while time.time() - start_time < restart_delay:
                try:
                    response = requests.get(qbittorrent_url, timeout=5)
                    if response.status_code in [200, 401, 403]:
                        container_up = True
                        elapsed = int(time.time() - start_time)
                        status_updates.append(f"Container is UP after {elapsed} seconds")
                        log_info(f"Container became accessible after {elapsed} seconds (fallback)")
                        break
                except requests.exceptions.RequestException:
                    pass
                
                time.sleep(2)
            
            if container_up:
                return jsonify({
                    'success': True,
                    'message': f'Successfully restarted {container_name} using fallback method',
                    'status_updates': status_updates
                })
            else:
                status_updates.append("Container failed to start even with fallback method")
                log_info("Container failed to start with fallback method")
                return jsonify({
                    'success': False,
                    'message': f'Failed to restart {container_name} - container not responding',
                    'status_updates': status_updates
                })
            
    except Exception as e:
        status_updates.append(f"Error: {str(e)}")
        log_info(f"Restart container error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Restart error: {str(e)}',
            'status_updates': status_updates
        })

# Global variable to track Prowlarr browser state
prowlarr_driver = None

@app.route('/api/prowlarr_login', methods=['POST'])
def api_prowlarr_login():
    """Login to Prowlarr web interface using Selenium"""
    log_info("Prowlarr Login request started")
    debug_info = []
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        global prowlarr_driver
        
        # Get Prowlarr settings
        settings = load_settings()
        log_debug(f"All settings keys: {list(settings.keys())}")
        prowlarr_url = settings.get('prowlarr_url', '')
        prowlarr_username = settings.get('prowlarr_username', '')
        prowlarr_password = settings.get('prowlarr_password', '')
        debug_info.append(f"Loaded prowlarr_url from settings: '{prowlarr_url}'")
        log_debug(f"prowlarr_url value: '{prowlarr_url}'")
        
        if not prowlarr_url:
            debug_info.append("Prowlarr URL not configured")
            debug_info.append(f"Settings keys available: {list(settings.keys())}")
            return jsonify({
                'success': False,
                'message': 'Prowlarr URL not configured. Please set in Config page.',
                'debug_info': debug_info
            })
        
        # Ensure URL has http:// prefix
        if not prowlarr_url.startswith('http'):
            prowlarr_url = 'http://' + prowlarr_url
        
        debug_info.append(f"Connecting to Prowlarr at: {prowlarr_url}")
        log_info(f"Connecting to Prowlarr at: {prowlarr_url}")
        
        # Create browser instance
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        prowlarr_driver = webdriver.Chrome(service=service, options=chrome_options)
        debug_info.append("Browser instance created")
        
        # Navigate to Prowlarr
        prowlarr_driver.get(prowlarr_url)
        time.sleep(3)
        debug_info.append(f"Navigated to {prowlarr_url}")
        
        # Check if login is required
        try:
            # Look for login form elements
            login_form = prowlarr_driver.find_elements(By.CSS_SELECTOR, 'input[type="text"], input[type="password"]')
            
            if login_form and prowlarr_username and prowlarr_password:
                debug_info.append("Login form detected, attempting authentication")
                log_info("Prowlarr requires authentication, logging in...")
                
                # Find username and password fields
                username_field = prowlarr_driver.find_element(By.CSS_SELECTOR, 'input[type="text"]')
                password_field = prowlarr_driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                
                username_field.clear()
                username_field.send_keys(prowlarr_username)
                password_field.clear()
                password_field.send_keys(prowlarr_password)
                
                # Submit login
                submit_button = prowlarr_driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
                submit_button.click()
                time.sleep(3)
                
                debug_info.append("Login submitted")
                log_info("Prowlarr login credentials submitted")
            elif not prowlarr_username or not prowlarr_password:
                debug_info.append("No credentials provided - assuming auth disabled for local network")
                log_debug("Prowlarr authentication skipped - no credentials configured")
            
        except Exception as login_error:
            debug_info.append(f"No login required or login error: {login_error}")
            log_debug(f"Prowlarr login check: {login_error}")
        
        # Verify page loaded
        page_title = prowlarr_driver.title
        debug_info.append(f"Page title: {page_title}")
        log_info(f"Prowlarr page loaded successfully: {page_title}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully connected to Prowlarr',
            'page_title': page_title,
            'debug_info': debug_info
        })
        
    except Exception as e:
        debug_info.append(f"Error connecting to Prowlarr: {str(e)}")
        log_info(f"Prowlarr login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to connect to Prowlarr: {str(e)}',
            'debug_info': debug_info
        })

@app.route('/api/prowlarr_send_cookie', methods=['POST'])
def api_prowlarr_send_cookie():
    """Update Prowlarr MyAnonamouse indexer with MAM session cookie"""
    log_info("Prowlarr Send Cookie request started")
    debug_info = []
    
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        
        global prowlarr_driver
        
        if not prowlarr_driver:
            debug_info.append("No active Prowlarr browser session")
            return jsonify({
                'success': False,
                'message': 'No active Prowlarr session. Please click "Log into Prowlarr" first.',
                'debug_info': debug_info
            })
        
        # Get Prowlarr cookie from settings
        settings = load_settings()
        prowlarr_cookie = settings.get('prowlarr_session_cookie', '')
        
        if not prowlarr_cookie or prowlarr_cookie == '0':
            debug_info.append("No Prowlarr cookie found")
            return jsonify({
                'success': False,
                'message': 'No Prowlarr cookie found. Please create one in Step 2 first.',
                'debug_info': debug_info
            })
        
        debug_info.append(f"Using Prowlarr cookie (length: {len(prowlarr_cookie)} chars)")
        log_info("Starting Prowlarr cookie update automation")
        
        # Step 1: Find MyAnonamouse indexer row
        debug_info.append("Step 1: Looking for MyAnonamouse indexer")
        log_debug("Searching for MyAnonamouse indexer in table")
        
        try:
            # Wait for table to load
            WebDriverWait(prowlarr_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table, div[class*='Table']"))
            )
            debug_info.append("Indexer table loaded")
            
            # Find all rows and look for MyAnonamouse
            rows = prowlarr_driver.find_elements(By.CSS_SELECTOR, "tr, div[class*='row']")
            debug_info.append(f"Found {len(rows)} rows to check")
            
            mam_row = None
            for row in rows:
                row_text = row.text.lower()
                if 'myanonamouse' in row_text:
                    mam_row = row
                    debug_info.append(f"Found MyAnonamouse row: {row.text[:100]}...")
                    log_info("MyAnonamouse indexer found")
                    break
            
            if not mam_row:
                debug_info.append("MyAnonamouse indexer not found in table")
                log_info("ERROR: MyAnonamouse indexer not found")
                return jsonify({
                    'success': False,
                    'message': 'MyAnonamouse indexer not found in Prowlarr',
                    'debug_info': debug_info
                })
            
        except TimeoutException:
            debug_info.append("Timeout waiting for indexer table")
            return jsonify({
                'success': False,
                'message': 'Timeout loading Prowlarr indexer table',
                'debug_info': debug_info
            })
        
        # Step 2: Click spanner/edit icon
        debug_info.append("Step 2: Clicking edit icon for MyAnonamouse")
        log_debug("Attempting to click edit button")
        
        try:
            # Find the edit button (spanner icon) in the row
            edit_button = mam_row.find_element(By.CSS_SELECTOR, 'button[aria-label="Table Options Button"][title="Edit Indexer"]')
            prowlarr_driver.execute_script("arguments[0].scrollIntoView(true);", edit_button)
            time.sleep(0.5)
            edit_button.click()
            debug_info.append("Edit button clicked")
            log_info("Edit Indexer button clicked")
            time.sleep(2)
            
        except NoSuchElementException:
            debug_info.append("Could not find edit button - trying alternative selector")
            try:
                # Try alternative selector
                edit_button = mam_row.find_element(By.CSS_SELECTOR, 'button[title="Edit Indexer"]')
                edit_button.click()
                debug_info.append("Edit button clicked (alternative selector)")
                time.sleep(2)
            except Exception as alt_error:
                debug_info.append(f"Failed to find edit button: {alt_error}")
                return jsonify({
                    'success': False,
                    'message': 'Could not find Edit button for MyAnonamouse',
                    'debug_info': debug_info
                })
        
        # Step 3: Wait for Edit Indexer popup
        debug_info.append("Step 3: Waiting for Edit Indexer popup")
        log_debug("Waiting for edit dialog to appear")
        
        try:
            # Wait for modal/dialog to appear
            WebDriverWait(prowlarr_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='Modal'], div[role='dialog'], form"))
            )
            debug_info.append("Edit popup appeared")
            log_info("Edit Indexer popup loaded")
            time.sleep(1)
            
        except TimeoutException:
            debug_info.append("Timeout waiting for edit popup")
            return jsonify({
                'success': False,
                'message': 'Edit Indexer popup did not appear',
                'debug_info': debug_info
            })
        
        # Step 4: Find and update Mam Id field
        debug_info.append("Step 4: Locating Mam Id field")
        log_debug("Searching for Mam Id input field")
        
        try:
            # Find the Mam Id input field
            # Try multiple strategies to find the field
            mam_id_field = None
            
            # Strategy 1: Look for input with label "Mam Id"
            try:
                labels = prowlarr_driver.find_elements(By.TAG_NAME, 'label')
                for label in labels:
                    if 'mam id' in label.text.lower():
                        # Find associated input
                        label_for = label.get_attribute('for')
                        if label_for:
                            mam_id_field = prowlarr_driver.find_element(By.ID, label_for)
                        break
            except:
                pass
            
            # Strategy 2: Look for input with name or id containing "mam"
            if not mam_id_field:
                inputs = prowlarr_driver.find_elements(By.CSS_SELECTOR, 'input[type="text"], input[type="password"]')
                for inp in inputs:
                    name = (inp.get_attribute('name') or '').lower()
                    id_attr = (inp.get_attribute('id') or '').lower()
                    if 'mam' in name or 'mam' in id_attr:
                        mam_id_field = inp
                        break
            
            if not mam_id_field:
                debug_info.append("Could not locate Mam Id field")
                return jsonify({
                    'success': False,
                    'message': 'Could not find Mam Id field in edit form',
                    'debug_info': debug_info
                })
            
            debug_info.append("Found Mam Id field")
            log_info("Mam Id field located")
            
            # Clear and enter new cookie
            mam_id_field.clear()
            mam_id_field.send_keys(prowlarr_cookie)
            debug_info.append(f"Entered Prowlarr cookie into Mam Id field")
            log_info("Prowlarr cookie entered into Mam Id field")
            time.sleep(1)
            
        except Exception as field_error:
            debug_info.append(f"Error updating Mam Id field: {field_error}")
            return jsonify({
                'success': False,
                'message': f'Failed to update Mam Id field: {str(field_error)}',
                'debug_info': debug_info
            })
        
        # Step 5: Click Test button and monitor result
        debug_info.append("Step 5: Clicking Test button")
        log_info("Testing Prowlarr cookie with Test button")
        
        test_result = 'unknown'
        try:
            # Find Test button
            test_buttons = prowlarr_driver.find_elements(By.CSS_SELECTOR, 'button')
            test_button = None
            for btn in test_buttons:
                if 'test' in btn.text.lower():
                    test_button = btn
                    break
            
            if not test_button:
                debug_info.append("Could not find Test button")
                test_result = 'button_not_found'
            else:
                debug_info.append("Found Test button, clicking...")
                test_button.click()
                log_debug("Test button clicked, monitoring for result")
                
                # Wait for button state change and monitor icon
                time.sleep(2)  # Wait for test to execute
                
                # Check button for success/failure icon
                try:
                    # Look for success indicators (green check, success class)
                    button_html = test_button.get_attribute('outerHTML')
                    button_class = test_button.get_attribute('class') or ''
                    
                    # Check for SVG icons in button
                    svgs = test_button.find_elements(By.TAG_NAME, 'svg')
                    for svg in svgs:
                        data_icon = svg.get_attribute('data-icon') or ''
                        if 'check' in data_icon or 'success' in data_icon:
                            test_result = 'success'
                            debug_info.append("Test SUCCESS - Green check icon detected")
                            log_info("✓ Prowlarr cookie test PASSED")
                            break
                        elif 'exclamation' in data_icon or 'error' in data_icon or 'times' in data_icon:
                            test_result = 'failure'
                            debug_info.append("Test FAILED - Error icon detected")
                            log_info("✗ Prowlarr cookie test FAILED")
                            break
                    
                    # Check button classes for success/error states
                    if test_result == 'unknown':
                        if 'success' in button_class.lower() or 'positive' in button_class.lower():
                            test_result = 'success'
                            debug_info.append("Test SUCCESS detected from button class")
                            log_info("✓ Prowlarr cookie test PASSED (class)")
                        elif 'error' in button_class.lower() or 'negative' in button_class.lower() or 'danger' in button_class.lower():
                            test_result = 'failure'
                            debug_info.append("Test FAILED detected from button class")
                            log_info("✗ Prowlarr cookie test FAILED (class)")
                    
                    debug_info.append(f"Button HTML sample: {button_html[:200]}...")
                    
                except Exception as icon_error:
                    debug_info.append(f"Could not detect test result icon: {icon_error}")
                    test_result = 'unknown'
                
                time.sleep(2)  # Wait for icon to be visible
                
        except Exception as test_error:
            debug_info.append(f"Error during test: {test_error}")
            test_result = 'error'
        
        # Report test result but continue to save
        if test_result == 'success':
            debug_info.append("✓ Test passed - cookie is valid")
        elif test_result == 'failure':
            debug_info.append("⚠ Test failed - but continuing to save anyway as requested")
        else:
            debug_info.append("⚠ Test result unclear - continuing to save anyway")
        
        # Step 6: Click Save button
        debug_info.append("Step 6: Clicking Save button")
        log_info("Saving Prowlarr indexer configuration")
        
        try:
            # Find Save button
            save_buttons = prowlarr_driver.find_elements(By.CSS_SELECTOR, 'button')
            save_button = None
            for btn in save_buttons:
                if 'save' in btn.text.lower():
                    save_button = btn
                    break
            
            if not save_button:
                debug_info.append("Could not find Save button")
                return jsonify({
                    'success': False,
                    'message': 'Could not find Save button',
                    'test_result': test_result,
                    'debug_info': debug_info
                })
            
            save_button.click()
            debug_info.append("Save button clicked")
            log_info("Save button clicked")
            time.sleep(3)  # Wait for save to complete
            
            debug_info.append("✓ Prowlarr cookie update completed")
            log_info("✓ Successfully updated Prowlarr MyAnonamouse indexer")
            
            return jsonify({
                'success': True,
                'message': f'Successfully updated Prowlarr cookie (Test: {test_result})',
                'test_result': test_result,
                'debug_info': debug_info
            })
            
        except Exception as save_error:
            debug_info.append(f"Error clicking Save button: {save_error}")
            return jsonify({
                'success': False,
                'message': f'Failed to save: {str(save_error)}',
                'test_result': test_result,
                'debug_info': debug_info
            })
        
    except Exception as e:
        debug_info.append(f"Unexpected error: {str(e)}")
        log_info(f"Prowlarr send cookie error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error updating Prowlarr cookie: {str(e)}',
            'debug_info': debug_info
        })

@app.route('/api/prowlarr_logout', methods=['POST'])
def api_prowlarr_logout():
    """Logout from Prowlarr by closing browser"""
    log_info("Prowlarr Logout request started")
    debug_info = []
    
    try:
        global prowlarr_driver
        
        if prowlarr_driver:
            try:
                prowlarr_driver.quit()
                debug_info.append("Browser closed")
                log_info("Prowlarr browser session closed")
                return jsonify({
                    'success': True,
                    'message': 'Successfully logged out from Prowlarr',
                    'debug_info': debug_info
                })
            except Exception as e:
                debug_info.append(f"Error closing browser: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error closing browser: {str(e)}',
                    'debug_info': debug_info
                })
            finally:
                prowlarr_driver = None
        else:
            debug_info.append("No active browser session")
            return jsonify({
                'success': True,
                'message': 'No active Prowlarr session to close',
                'debug_info': debug_info
            })
            
    except Exception as e:
        debug_info.append(f"Error during logout: {str(e)}")
        log_info(f"Prowlarr logout error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Logout error: {str(e)}',
            'debug_info': debug_info
        })

# Basic Mode Orchestration Endpoints

@app.route('/api/fix_myanonamouse', methods=['POST'])
def api_fix_myanonamouse():
    """Orchestrate Fix MyAnonamouse workflow"""
    log_info("Fix MyAnonamouse orchestration started")
    steps = []
    overall_success = True
    
    try:
        # Step 1: Clear Cookies
        log_info("Step 1: Clear Cookies")
        try:
            response = api_clear_cookies()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Clear Cookies', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Clear Cookies: Success")
            else:
                steps.append({'name': 'Clear Cookies', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Clear Cookies: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Clear Cookies', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Clear Cookies error: {e}")
            overall_success = False
        
        # Step 2: Restart qBittorrent Container
        log_info("Step 2: Restart qBittorrent Container")
        try:
            response = api_restart_qbittorrent_container()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Restart qBittorrent', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Restart qBittorrent: Success")
            else:
                steps.append({'name': 'Restart qBittorrent', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Restart qBittorrent: {data['message']}")
                overall_success = False
                # Critical failure - stop here
                return jsonify({
                    'success': False,
                    'message': 'Fix MyAnonamouse failed: Could not restart qBittorrent container',
                    'steps': steps
                })
        except Exception as e:
            steps.append({'name': 'Restart qBittorrent', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Restart qBittorrent error: {e}")
            return jsonify({
                'success': False,
                'message': f'Fix MyAnonamouse failed: {str(e)}',
                'steps': steps
            })
        
        # Step 3: Wait 30 seconds
        log_info("Step 3: Waiting 30 seconds...")
        steps.append({'name': 'Wait 30 seconds', 'status': 'SUCCESS', 'message': 'Waiting for container to stabilize'})
        time.sleep(30)
        
        # Step 4: Get IPs
        log_info("Step 4: Get IPs")
        try:
            response = api_get_ips()
            data = response.get_json()
            if data.get('external_ip') and data.get('vpn_ip'):
                steps.append({'name': 'Get IPs', 'status': 'SUCCESS', 'message': f"External: {data['external_ip']}, VPN: {data['vpn_ip']}"})
                log_info(f"✓ Get IPs: External={data['external_ip']}, VPN={data['vpn_ip']}")
            else:
                steps.append({'name': 'Get IPs', 'status': 'FAILED', 'message': 'Could not retrieve IPs'})
                log_info("✗ Get IPs: Failed to retrieve")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Get IPs', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Get IPs error: {e}")
            overall_success = False
        
        # Step 5: Create qBittorrent Session
        log_info("Step 5: Create qBittorrent Session")
        try:
            response = api_create_qbittorrent_cookie()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Create qBittorrent Session', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Create qBittorrent Session: Success")
            else:
                steps.append({'name': 'Create qBittorrent Session', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Create qBittorrent Session: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Create qBittorrent Session', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Create qBittorrent Session error: {e}")
            overall_success = False
        
        # Step 6: Logout MAM
        log_info("Step 6: Logout MAM")
        try:
            response = api_logout_mam()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Logout MAM', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Logout MAM: Success")
            else:
                steps.append({'name': 'Logout MAM', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Logout MAM: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Logout MAM', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Logout MAM error: {e}")
            overall_success = False
        
        # Step 7: Log into qBittorrent
        log_info("Step 7: Log into qBittorrent")
        try:
            response = api_qbittorrent_login()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Login qBittorrent', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Login qBittorrent: Success")
            else:
                steps.append({'name': 'Login qBittorrent', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Login qBittorrent: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Login qBittorrent', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Login qBittorrent error: {e}")
            overall_success = False
        
        # Step 8: Send Cookie to qBittorrent
        log_info("Step 8: Send Cookie to qBittorrent")
        try:
            response = api_qbittorrent_send_cookie()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Send Cookie to qBittorrent', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Send Cookie to qBittorrent: Success")
            else:
                steps.append({'name': 'Send Cookie to qBittorrent', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Send Cookie to qBittorrent: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Send Cookie to qBittorrent', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Send Cookie to qBittorrent error: {e}")
            overall_success = False
        
        # Step 9: Logout qBittorrent
        log_info("Step 9: Logout qBittorrent")
        try:
            response = api_qbittorrent_logout()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Logout qBittorrent', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Logout qBittorrent: Success")
            else:
                steps.append({'name': 'Logout qBittorrent', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Logout qBittorrent: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Logout qBittorrent', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Logout qBittorrent error: {e}")
            overall_success = False
        
        # Final result
        if overall_success:
            log_info("Fix MyAnonamouse completed successfully")
            return jsonify({
                'success': True,
                'message': 'Fix MyAnonamouse completed successfully',
                'steps': steps
            })
        else:
            log_info("Fix MyAnonamouse completed with some failures")
            return jsonify({
                'success': False,
                'message': 'Fix MyAnonamouse completed with some failures',
                'steps': steps
            })
            
    except Exception as e:
        log_info(f"Fix MyAnonamouse orchestration error: {e}")
        return jsonify({
            'success': False,
            'message': f'Orchestration error: {str(e)}',
            'steps': steps
        })

@app.route('/api/fix_prowlarr', methods=['POST'])
def api_fix_prowlarr():
    """Orchestrate Fix Prowlarr workflow"""
    log_info("Fix Prowlarr orchestration started")
    steps = []
    overall_success = True
    
    try:
        # Step 1: Clear Cookies
        log_info("Step 1: Clear Cookies")
        try:
            response = api_clear_cookies()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Clear Cookies', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Clear Cookies: Success")
            else:
                steps.append({'name': 'Clear Cookies', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Clear Cookies: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Clear Cookies', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Clear Cookies error: {e}")
            overall_success = False
        
        # Step 2: Get IPs
        log_info("Step 2: Get IPs")
        try:
            response = api_get_ips()
            data = response.get_json()
            if data.get('external_ip') and data.get('vpn_ip'):
                steps.append({'name': 'Get IPs', 'status': 'SUCCESS', 'message': f"External: {data['external_ip']}, VPN: {data['vpn_ip']}"})
                log_info(f"✓ Get IPs: External={data['external_ip']}, VPN={data['vpn_ip']}")
            else:
                steps.append({'name': 'Get IPs', 'status': 'FAILED', 'message': 'Could not retrieve IPs'})
                log_info("✗ Get IPs: Failed to retrieve")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Get IPs', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Get IPs error: {e}")
            overall_success = False
        
        # Step 3: Create Prowlarr Session
        log_info("Step 3: Create Prowlarr Session")
        try:
            response = api_create_prowlarr_cookie()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Create Prowlarr Session', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Create Prowlarr Session: Success")
            else:
                steps.append({'name': 'Create Prowlarr Session', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Create Prowlarr Session: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Create Prowlarr Session', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Create Prowlarr Session error: {e}")
            overall_success = False
        
        # Step 4: Logout MAM
        log_info("Step 4: Logout MAM")
        try:
            response = api_logout_mam()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Logout MAM', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Logout MAM: Success")
            else:
                steps.append({'name': 'Logout MAM', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Logout MAM: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Logout MAM', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Logout MAM error: {e}")
            overall_success = False
        
        # Step 5: Log into Prowlarr
        log_info("Step 5: Log into Prowlarr")
        try:
            response = api_prowlarr_login()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Login Prowlarr', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Login Prowlarr: Success")
            else:
                steps.append({'name': 'Login Prowlarr', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Login Prowlarr: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Login Prowlarr', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Login Prowlarr error: {e}")
            overall_success = False
        
        # Step 6: Send Cookie to Prowlarr
        log_info("Step 6: Send Cookie to Prowlarr")
        try:
            response = api_prowlarr_send_cookie()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Send Cookie to Prowlarr', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Send Cookie to Prowlarr: Success")
            else:
                steps.append({'name': 'Send Cookie to Prowlarr', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Send Cookie to Prowlarr: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Send Cookie to Prowlarr', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Send Cookie to Prowlarr error: {e}")
            overall_success = False
        
        # Step 7: Logout Prowlarr
        log_info("Step 7: Logout Prowlarr")
        try:
            response = api_prowlarr_logout()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Logout Prowlarr', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Logout Prowlarr: Success")
            else:
                steps.append({'name': 'Logout Prowlarr', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Logout Prowlarr: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Logout Prowlarr', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Logout Prowlarr error: {e}")
            overall_success = False
        
        # Final result
        if overall_success:
            log_info("Fix Prowlarr completed successfully")
            return jsonify({
                'success': True,
                'message': 'Fix Prowlarr completed successfully',
                'steps': steps
            })
        else:
            log_info("Fix Prowlarr completed with some failures")
            return jsonify({
                'success': False,
                'message': 'Fix Prowlarr completed with some failures',
                'steps': steps
            })
            
    except Exception as e:
        log_info(f"Fix Prowlarr orchestration error: {e}")
        return jsonify({
            'success': False,
            'message': f'Orchestration error: {str(e)}',
            'steps': steps
        })

@app.route('/api/fix_all', methods=['POST'])
def api_fix_all():
    """Orchestrate Fix All workflow"""
    log_info("Fix All orchestration started")
    steps = []
    overall_success = True
    
    try:
        # Step 1: Clear Cookies
        log_info("Step 1: Clear Cookies")
        try:
            response = api_clear_cookies()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Clear Cookies', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Clear Cookies: Success")
            else:
                steps.append({'name': 'Clear Cookies', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Clear Cookies: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Clear Cookies', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Clear Cookies error: {e}")
            overall_success = False
        
        # Step 2: Restart qBittorrent Container
        log_info("Step 2: Restart qBittorrent Container")
        try:
            response = api_restart_qbittorrent_container()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Restart qBittorrent', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Restart qBittorrent: Success")
            else:
                steps.append({'name': 'Restart qBittorrent', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Restart qBittorrent: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Restart qBittorrent', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Restart qBittorrent error: {e}")
            overall_success = False
        
        # Step 3: Wait 30 seconds
        log_info("Step 3: Waiting 30 seconds...")
        steps.append({'name': 'Wait 30 seconds', 'status': 'SUCCESS', 'message': 'Waiting for container to stabilize'})
        time.sleep(30)
        
        # Step 4: Get IPs
        log_info("Step 4: Get IPs")
        try:
            response = api_get_ips()
            data = response.get_json()
            if data.get('external_ip') and data.get('vpn_ip'):
                steps.append({'name': 'Get IPs', 'status': 'SUCCESS', 'message': f"External: {data['external_ip']}, VPN: {data['vpn_ip']}"})
                log_info(f"✓ Get IPs: External={data['external_ip']}, VPN={data['vpn_ip']}")
            else:
                steps.append({'name': 'Get IPs', 'status': 'FAILED', 'message': 'Could not retrieve IPs'})
                log_info("✗ Get IPs: Failed to retrieve")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Get IPs', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Get IPs error: {e}")
            overall_success = False
        
        # Step 5: Delete old sessions
        log_info("Step 5: Delete old sessions")
        try:
            response = api_delete_old_sessions()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Delete Old Sessions', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Delete Old Sessions: Success")
            else:
                steps.append({'name': 'Delete Old Sessions', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Delete Old Sessions: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Delete Old Sessions', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Delete Old Sessions error: {e}")
            overall_success = False
        
        # Step 6: Create qBittorrent Session
        log_info("Step 6: Create qBittorrent Session")
        try:
            response = api_create_qbittorrent_cookie()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Create qBittorrent Session', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Create qBittorrent Session: Success")
            else:
                steps.append({'name': 'Create qBittorrent Session', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Create qBittorrent Session: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Create qBittorrent Session', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Create qBittorrent Session error: {e}")
            overall_success = False
        
        # Step 7: Create Prowlarr Session
        log_info("Step 7: Create Prowlarr Session")
        try:
            response = api_create_prowlarr_cookie()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Create Prowlarr Session', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Create Prowlarr Session: Success")
            else:
                steps.append({'name': 'Create Prowlarr Session', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Create Prowlarr Session: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Create Prowlarr Session', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Create Prowlarr Session error: {e}")
            overall_success = False
        
        # Step 8: Logout MAM
        log_info("Step 8: Logout MAM")
        try:
            response = api_logout_mam()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Logout MAM', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Logout MAM: Success")
            else:
                steps.append({'name': 'Logout MAM', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Logout MAM: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Logout MAM', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Logout MAM error: {e}")
            overall_success = False
        
        # Step 9: Log into qBittorrent
        log_info("Step 9: Log into qBittorrent")
        try:
            response = api_qbittorrent_login()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Login qBittorrent', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Login qBittorrent: Success")
            else:
                steps.append({'name': 'Login qBittorrent', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Login qBittorrent: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Login qBittorrent', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Login qBittorrent error: {e}")
            overall_success = False
        
        # Step 10: Send Cookie to qBittorrent
        log_info("Step 10: Send Cookie to qBittorrent")
        try:
            response = api_qbittorrent_send_cookie()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Send Cookie to qBittorrent', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Send Cookie to qBittorrent: Success")
            else:
                steps.append({'name': 'Send Cookie to qBittorrent', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Send Cookie to qBittorrent: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Send Cookie to qBittorrent', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Send Cookie to qBittorrent error: {e}")
            overall_success = False
        
        # Step 11: Logout qBittorrent
        log_info("Step 11: Logout qBittorrent")
        try:
            response = api_qbittorrent_logout()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Logout qBittorrent', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Logout qBittorrent: Success")
            else:
                steps.append({'name': 'Logout qBittorrent', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Logout qBittorrent: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Logout qBittorrent', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Logout qBittorrent error: {e}")
            overall_success = False
        
        # Step 12: Log into Prowlarr
        log_info("Step 12: Log into Prowlarr")
        try:
            response = api_prowlarr_login()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Login Prowlarr', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Login Prowlarr: Success")
            else:
                steps.append({'name': 'Login Prowlarr', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Login Prowlarr: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Login Prowlarr', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Login Prowlarr error: {e}")
            overall_success = False
        
        # Step 13: Send Cookie to Prowlarr
        log_info("Step 13: Send Cookie to Prowlarr")
        try:
            response = api_prowlarr_send_cookie()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Send Cookie to Prowlarr', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Send Cookie to Prowlarr: Success")
            else:
                steps.append({'name': 'Send Cookie to Prowlarr', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Send Cookie to Prowlarr: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Send Cookie to Prowlarr', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Send Cookie to Prowlarr error: {e}")
            overall_success = False
        
        # Step 14: Logout Prowlarr
        log_info("Step 14: Logout Prowlarr")
        try:
            response = api_prowlarr_logout()
            data = response.get_json()
            if data['success']:
                steps.append({'name': 'Logout Prowlarr', 'status': 'SUCCESS', 'message': data['message']})
                log_info("✓ Logout Prowlarr: Success")
            else:
                steps.append({'name': 'Logout Prowlarr', 'status': 'FAILED', 'message': data['message']})
                log_info(f"✗ Logout Prowlarr: {data['message']}")
                overall_success = False
        except Exception as e:
            steps.append({'name': 'Logout Prowlarr', 'status': 'ERROR', 'message': str(e)})
            log_info(f"✗ Logout Prowlarr error: {e}")
            overall_success = False
        
        # Save to history
        save_run_to_history(overall_success, steps)
        
        # Final result
        if overall_success:
            log_info("Fix All completed successfully")
            return jsonify({
                'success': True,
                'message': 'Fix All completed successfully',
                'steps': steps
            })
        else:
            log_info("Fix All completed with some failures")
            return jsonify({
                'success': False,
                'message': 'Fix All completed with some failures',
                'steps': steps
            })
            
    except Exception as e:
        log_info(f"Fix All orchestration error: {e}")
        return jsonify({
            'success': False,
            'message': f'Orchestration error: {str(e)}',
            'steps': steps
        })

# Timer state management
timer_state = {
    'active': False,
    'next_run': None,
    'last_run': None,
    'history': []  # List of last 10 runs
}
timer_thread = None
timer_lock = __import__('threading').Lock()

def save_run_to_history(success, steps):
    """Save run result to history"""
    from datetime import datetime
    
    with timer_lock:
        # Determine status
        if success:
            status = 'Success'
        else:
            failed_steps = [s for s in steps if s['status'] in ['FAILED', 'ERROR']]
            if failed_steps:
                status = 'Partial'
            else:
                status = 'Failed'
        
        # Create history entry
        entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': status,
            'details': f"{len([s for s in steps if s['status'] == 'SUCCESS'])}/{len(steps)} steps succeeded"
        }
        
        # Add to history (keep last 10)
        timer_state['history'].insert(0, entry)
        if len(timer_state['history']) > 10:
            timer_state['history'] = timer_state['history'][:10]
        
        # Update last run time
        timer_state['last_run'] = entry['timestamp']
        
        log_info(f"Run saved to history: {status} - {entry['details']}")

def calculate_next_run_time():
    """Calculate next run time with jitter"""
    from datetime import datetime, timedelta
    import random
    
    settings = load_settings()
    scheduled_time = settings.get('scheduled_run_time', '02:00')
    jitter_minutes = int(settings.get('jitter_minutes', 10))
    
    log_debug(f"Calculating next run time: scheduled={scheduled_time}, jitter=±{jitter_minutes}")
    
    # Parse scheduled time
    hour, minute = map(int, scheduled_time.split(':'))
    
    # Get tomorrow's date at scheduled time
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If scheduled time already passed today, use tomorrow
    if next_run <= now:
        next_run = next_run + timedelta(days=1)
    
    # Add random jitter
    jitter_offset = random.randint(-jitter_minutes, jitter_minutes)
    next_run = next_run + timedelta(minutes=jitter_offset)
    
    log_info(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (jitter: {jitter_offset:+d} minutes)")
    
    return next_run

def timer_worker():
    """Background thread for timer"""
    log_info("Timer worker thread started")
    
    while True:
        try:
            with timer_lock:
                if not timer_state['active']:
                    log_debug("Timer inactive, stopping worker thread")
                    break
                
                next_run = timer_state.get('next_run')
            
            if next_run:
                from datetime import datetime
                now = datetime.now()
                next_run_dt = datetime.strptime(next_run, '%Y-%m-%d %H:%M:%S')
                
                if now >= next_run_dt:
                    log_info("Timer triggered - running Fix All")
                    
                    # Run Fix All
                    with app.test_request_context():
                        try:
                            api_fix_all()
                        except Exception as e:
                            log_info(f"Timer execution error: {e}")
                    
                    # Calculate next run time
                    next_run_dt = calculate_next_run_time()
                    with timer_lock:
                        timer_state['next_run'] = next_run_dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    log_info(f"Next run scheduled: {timer_state['next_run']}")
            
            # Check every 30 seconds
            time.sleep(30)
            
        except Exception as e:
            log_info(f"Timer worker error: {e}")
            time.sleep(30)
    
    log_info("Timer worker thread stopped")

@app.route('/api/timer_status', methods=['GET'])
def api_timer_status():
    """Get timer status"""
    with timer_lock:
        return jsonify({
            'active': timer_state['active'],
            'next_run': timer_state.get('next_run'),
            'last_run': timer_state.get('last_run'),
            'history': timer_state.get('history', [])
        })

@app.route('/api/timer_toggle', methods=['POST'])
def api_timer_toggle():
    """Toggle timer on/off"""
    global timer_thread
    
    data = request.json
    new_state = data.get('active', False)
    
    log_info(f"Timer toggle requested: {new_state}")
    
    with timer_lock:
        timer_state['active'] = new_state
        
        if new_state:
            # Calculate next run time
            next_run_dt = calculate_next_run_time()
            timer_state['next_run'] = next_run_dt.strftime('%Y-%m-%d %H:%M:%S')
            log_info(f"Timer activated - next run: {timer_state['next_run']}")
            
            # Start timer thread
            if timer_thread is None or not timer_thread.is_alive():
                import threading
                timer_thread = threading.Thread(target=timer_worker, daemon=True)
                timer_thread.start()
                log_info("Timer worker thread started")
        else:
            timer_state['next_run'] = None
            log_info("Timer deactivated")
    
    return jsonify({
        'success': True,
        'message': f"Timer {'activated' if new_state else 'deactivated'}",
        'next_run': timer_state.get('next_run')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
