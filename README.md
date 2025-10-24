# MAMRenewARR

Automated MyAnonamouse session management for qBittorrent and Prowlarr. Keeps your torrent clients connected to MAM with automatic cookie renewal and session management.

**Created by Ahazi** | [GitHub Repository](https://github.com/Ahazii/MAMRenewARR)

---

## Key Features

- 🤖 **Automated Timer** - Schedule daily/weekly runs with jitter and timezone support
- 🔄 **Auto-Restart** - Timer persists through container restarts
- 📊 **Run History** - Track last 10 automated runs
- 🟢 **Progress Bars** - Real-time visual feedback for all operations
- 📊 **Status Tracking** - Persistent footer shows last cookie push status and mode
- 🎯 **Basic Mode** - One-click fixes for qBittorrent and Prowlarr
- 🔧 **Advanced Mode** - Step-by-step manual control with progress indicators
- 🌐 **Web Interface** - Clean UI with light/dark themes
- 📝 **Log Viewer** - Web-based log viewer with auto-refresh
- 🔧 **Configurable Port** - Change port via environment variable
- 💾 **Persistent Storage** - All settings and history saved

---

## Quick Start

### Unraid (Recommended)

1. Go to **Docker** tab → **Add Container**
2. Search for `MAMRenewARR` in Community Applications
3. Or manually add template URL:
   ```
   https://raw.githubusercontent.com/Ahazii/MAMRenewARR/main/mamrenewarr.xml
   ```
4. Configure settings and click **Apply**

### Manual Installation

```bash
docker run -d --name mamrenewarr \
  -p 5000:5000 \
  -e TZ=Europe/London \
  -e PORT=5000 \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  -v /etc/localtime:/etc/localtime:ro \
  --restart unless-stopped \
  ghcr.io/ahazii/mamrenewarr:main
```

**Access**: `http://YOUR-UNRAID-IP:5000`

**Notes**: 
- Replace `Europe/London` with your timezone
- Change port with `-p 8080:5000 -e PORT=5000` (maps host port 8080 to container port 5000)

---

## Usage

### Basic Mode (Recommended)
1. Go to **Config** page and enter your MAM credentials
2. Configure timer settings (schedule, interval, jitter)
3. Go to **Basic Mode**
4. Click "Fix All" to run full workflow once
5. Enable timer toggle for automation
6. Check "Auto-start timer on container restart" to persist

### Advanced Mode
- Step-by-step manual control of each operation
- Useful for testing or troubleshooting
- View detailed logs for each step

### Logs Page
- View application logs in real-time
- Auto-refresh every 5 seconds
- Adjustable line count (100-1000 or all)
- Located at: `http://YOUR-IP:5000/logs`

### Timer Configuration (Config Page)
- **Scheduled Run Time**: When to run (HH:MM, 24-hour format)
- **Jitter**: Random variance ±N minutes
- **Run Interval**: Days between runs (1=daily, 7=weekly, 30=monthly)

---

## Requirements

- Docker with socket access (`/var/run/docker.sock`)
- `binhex-qbittorrentvpn` container (for qBittorrent)
- Port 5000 available (or custom via `-e PORT=XXXX`)
- MyAnonamouse account with credentials

---

## Configuration

### Port Configuration
Change the application port using the `PORT` environment variable:
```bash
-p 8080:8080 -e PORT=8080
```

### Log Files
- Location: `/app/data/mamrenewarr.log`
- Rotation: 10MB per file, keeps last 5 files (50MB total)
- Levels: Info (default) or Debug (set in Config page)

---

## License

MIT License | Created by Ahazi | [Report Issues](https://github.com/Ahazii/MAMRenewARR/issues)
