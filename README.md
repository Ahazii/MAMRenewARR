# MAMRenewARR

Automated MyAnonamouse session management for qBittorrent and Prowlarr. Keeps your torrent clients connected to MAM with automatic cookie renewal and session management.

**Created by Ahazi** | [GitHub Repository](https://github.com/Ahazii/MAMRenewARR)

---

## Key Features

- 🤖 **Automated Timer** - Schedule daily/weekly runs with jitter and timezone support
- 🔄 **Auto-Restart** - Timer persists through container restarts
- 📊 **Run History** - Track last 10 automated runs
- 🎯 **Basic Mode** - One-click fixes for qBittorrent and Prowlarr
- 🔧 **Advanced Mode** - Step-by-step manual control
- 🌐 **Web Interface** - Clean UI with light/dark themes
- 📝 **Logging** - Configurable debug/info levels
- 💾 **Persistent Storage** - All settings and history saved

---

## Quick Start

```bash
cd /mnt/user/appdata
git clone https://github.com/Ahazii/MAMRenewARR
cd MAMRenewARR
docker build -t mamrenewarr:latest .
docker run -d --name mamrenewarr -p 5000:5000 \
  -e TZ=Europe/London \
  -v /etc/localtime:/etc/localtime:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  --restart unless-stopped mamrenewarr:latest
```

**Access**: `http://YOUR-UNRAID-IP:5000`

**Note**: Replace `Europe/London` with your timezone

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

### Timer Configuration (Config Page)
- **Scheduled Run Time**: When to run (HH:MM, 24-hour format)
- **Jitter**: Random variance ±N minutes
- **Run Interval**: Days between runs (1=daily, 7=weekly, 30=monthly)

---

## Requirements

- Docker with socket access (`/var/run/docker.sock`)
- `binhex-qbittorrentvpn` container (for qBittorrent)
- Port 5000 available
- MyAnonamouse account with credentials

---

## License

MIT License | Created by Ahazi | [Report Issues](https://github.com/Ahazii/MAMRenewARR/issues)
