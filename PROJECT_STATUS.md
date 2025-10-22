# MAMRenewARR Project Status

## Current State (Latest Update)

### ✅ Completed Features

#### 1. Core Infrastructure
- Docker containerization with production-ready setup
- Flask web application with proper error handling
- Cross-platform compatibility (Windows/Linux/Unraid)
- Persistent data storage via mounted volumes

#### 2. Web Interface
- **Basic Mode**: Simple interface for quick operations
- **Advanced Mode**: Step-by-step workflow with detailed controls
- **Config Page**: Settings management with form validation
- **Theme System**: Light/Dark mode toggle with persistence
- **Responsive Design**: Mobile-friendly layout

#### 3. MAM Integration (Selenium-based)
- **Login Automation**: Browser-based login with session handling
- **Session Cookie Creation**: Automated cookie generation for qBittorrent/Prowlarr
- **Old Session Cleanup**: Automated removal of expired sessions with dialog handling
- **Page Viewer**: Real browser window for MAM navigation
- **Cookie Timestamps**: Date/time tracking for session creation
- **Logout & Clear Functions**: MAM logout and cookie clearing capabilities
- **Rate Limit Detection**: User-friendly error messages for MAM rate limits

#### 4. IP Detection System
- **External IP**: Public IP address detection
- **VPN IP**: Container IP extraction from qBittorrentVPN logs
- **Status Tracking**: Visual indicators for IP detection state

#### 5. Settings Persistence
- **Configuration Storage**: All settings saved to `settings.json`
- **Cookie Storage**: Session cookies with timestamps
- **Log Level Management**: Configurable logging with persistence
- **Auto-loading**: Settings restored on application restart

#### 6. qBittorrent & Prowlarr Integration
- **Container Communication**: Docker exec commands to `binhex-qbittorrentvpn`
- **Connection Management**: Container connection state tracking
- **Curl Command Execution**: MAM dynamic seedbox API calls with session cookies
- **Response Validation**: Parse MAM API responses with rate limit detection
- **Docker CLI Integration**: Full Docker CLI available in container
- **Socket Mounting**: Secure Docker daemon communication via socket
- **Prowlarr Integration**: Complete Selenium-based Prowlarr cookie management

#### 7. Timer & Scheduling System
- **Configurable Timer**: Automated task scheduling with persistence
- **Run Interval**: Configurable days between runs (daily/weekly/monthly)
- **Jitter Support**: Random variance to prevent predictable scheduling patterns
- **Timezone Handling**: Proper timezone support with automatic DST transitions
- **Run History**: Track last 10 runs with success/failure status
- **Thread Management**: Robust background worker with heartbeat logging

#### 8. Logging & Debugging
- **Dual Output**: Console and file logging with rotation
- **Configurable Levels**: Info/Debug modes with runtime switching
- **Duplicate Fix**: Single log entries (no more double logging)
- **Structured Logs**: Timestamped entries with log levels

### 🔧 Technical Implementation Details

#### Backend (Flask)
- **Route Structure**: RESTful API endpoints for all operations
- **Error Handling**: Comprehensive exception catching and logging
- **Session Management**: Selenium WebDriver with proper cleanup
- **File Operations**: Safe file I/O with error recovery
- **Logging System**: Configurable log levels with file output

#### Frontend (JavaScript/HTML)
- **Event Handling**: Button interactions with loading states
- **AJAX Operations**: Asynchronous API calls with error handling
- **UI Updates**: Dynamic content updates and status indicators
- **Form Validation**: Client and server-side validation
- **Theme Persistence**: Local storage for user preferences

#### Selenium Integration
- **WebDriver Management**: Chrome WebDriver with headless option
- **Element Detection**: Robust CSS selectors with fallback logic
- **Dialog Handling**: Confirmation dialog detection and interaction
- **Cookie Extraction**: Session cookie parsing and validation
- **Error Recovery**: Graceful handling of page load failures

### 🏗️ Architecture

#### File Structure
```
MAMRenewARR/
├── app.py                 # Main Flask application
├── templates/
│   ├── base.html         # Base template with theme system
│   ├── index.html        # Basic mode interface
│   ├── advanced.html     # Advanced mode interface
│   └── config.html       # Configuration page
├── static/
│   ├── style.css         # Application styling
│   └── script.js         # Frontend JavaScript
├── data/
│   ├── settings.json     # Persistent configuration
│   └── logs/            # Application logs
├── Dockerfile           # Container build instructions
├── requirements.txt     # Python dependencies
└── README.md           # Project documentation
```

#### API Endpoints
- `GET /` - Basic mode interface
- `GET /advanced` - Advanced mode interface  
- `GET /config` - Configuration page
- `POST /api/get_ips` - IP detection
- `POST /api/login_mam` - MAM login
- `GET /api/view_mam` - MAM page viewer
- `POST /api/logout_mam` - MAM logout
- `POST /api/clear_cookies` - Clear session cookies
- `POST /api/create_qbittorrent_cookie` - qBittorrent cookie creation
- `POST /api/create_prowlarr_cookie` - Prowlarr cookie creation
- `POST /api/delete_old_sessions` - Session cleanup
- `POST /api/qbittorrent_login` - qBittorrent container connection
- `POST /api/qbittorrent_send_cookie` - Send cookie via curl to qBittorrent
- `POST /api/qbittorrent_logout` - qBittorrent container disconnect
- `POST /api/prowlarr_login` - Prowlarr web interface login
- `POST /api/prowlarr_send_cookie` - Send cookie to Prowlarr
- `POST /api/prowlarr_logout` - Prowlarr logout
- `POST /api/restart_qbittorrent_container` - Container restart with health check
- `POST /api/fix_qbittorrent` - Orchestrated qBittorrent workflow
- `POST /api/fix_prowlarr` - Orchestrated Prowlarr workflow
- `POST /api/fix_all` - Complete automated workflow
- `GET /api/timer_status` - Timer state and next run time
- `POST /api/timer_toggle` - Enable/disable timer
- `POST /api/save_config` - Settings persistence
- `GET /api/load_config` - Settings retrieval

### 🐛 Known Issues (All Fixed)
- ~~CSS selector bug with `[role='dialog']` causing InvalidSelectorException~~
- ~~VPN IP detection not working for qBittorrent cookie creation~~
- ~~Settings not persisting between application restarts~~
- ~~Cookie timestamps not displaying in UI~~
- ~~Duplicate log entries appearing in container logs and files~~
- ~~Timer scheduling next run for same day instead of next interval~~
- ~~Timezone not properly handled, causing time mismatches~~

### 🚀 Ready for Production
The application is fully functional and ready for deployment:

1. **Pull latest code**: `git pull origin main`
2. **Build container**: `docker build -t mamrenewarr:latest .`
3. **Deploy with Docker socket and timezone**: 
   ```bash
   docker run -d --name mamrenewarr -p 5000:5000 \
     -e TZ=Europe/London \
     -v /etc/localtime:/etc/localtime:ro \
     -v /mnt/user/appdata/MAMRenewARR:/app/data \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
     --restart unless-stopped mamrenewarr:latest
   ```
4. **Configure Timer** (optional): Set run interval, jitter, and scheduled time in Config page
5. **Test**: All features working - Basic Mode, Advanced Mode, and Timer automation

### 📝 Future Enhancements (Optional)
- **Enhanced error reporting** with retry logic and exponential backoff
- **Additional torrent client integrations** (Transmission, Deluge, etc.)
- **Performance optimizations** and response caching
- **Unit test coverage** for critical functions
- **Web UI improvements** with real-time status updates
- **Multi-user support** with authentication
- **Notification system** (email, webhook, Discord, etc.)

---

**Project Repository**: https://github.com/Ahazii/MAMRenewARR  
**Docker Registry**: Available for container deployment  
**Status**: Production Ready ✅