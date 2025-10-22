# MAMRenewARR - Deployment Instructions

## Latest Updates

1. **Timer Interval Configuration**: Added configurable run interval (daily, weekly, etc.)
2. **Timezone Support**: Proper timezone handling with automatic DST transitions
3. **Duplicate Logging Fixed**: No more double log entries
4. **MAM Rate Limit Detection**: User-friendly error messages for rate limits
5. **Configuration Persistence**: Settings save to `/app/data/settings.json`
6. **VPN IP Detection**: Improved detection with multiple fallback methods

## Updated Deployment Commands

### Stop and Remove Current Container
```bash
docker stop mamrenewarr
docker rm mamrenewarr
```

### Rebuild Image with Fixes
```bash
cd /mnt/user/appdata/MAMRenewARR
git pull origin main
docker build -t mamrenewarr:latest .
```

### Run Updated Container
```bash
docker run -d \
  --name mamrenewarr \
  -p 5000:5000 \
  -e TZ=Europe/London \
  -v /etc/localtime:/etc/localtime:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  --restart unless-stopped \
  mamrenewarr:latest
```

**Note**: Replace `Europe/London` with your timezone (e.g., `America/New_York`, `Asia/Tokyo`)

## Important Configuration Notes

### Timezone Configuration

The container now supports proper timezone handling:
- Set via `-e TZ=Your/Timezone` environment variable
- Automatically handles DST transitions (e.g., British Summer Time)
- Required for accurate timer scheduling

**Common Timezones**:
- UK: `Europe/London` (auto-handles BST)
- US East: `America/New_York`
- US West: `America/Los_Angeles`
- Europe: `Europe/Paris`, `Europe/Berlin`
- Asia: `Asia/Tokyo`, `Asia/Singapore`

### Timer Settings (in Config page)

1. **Scheduled Run Time**: When to run daily tasks (HH:MM format, 24-hour)
2. **Jitter (minutes)**: Random variance ±N minutes to prevent predictable patterns
3. **Run Interval (days)**: How many days between runs
   - `1` = Run daily
   - `7` = Run weekly
   - `30` = Run monthly

### VPN IP Detection Options

The updated container supports multiple methods for VPN IP detection:

1. **Log File Method**: Mount your qBittorrent VPN container's log directory
   ```bash
   # Example with additional volume mount for qBittorrent logs
   docker run -d \
     --name mamrenewarr \
     -p 5000:5000 \
     -v /mnt/user/appdata/MAMRenewARR:/app/data \
     -v /mnt/user/appdata/binhex-qbittorrentvpn/config/qBittorrent/data/logs:/shared/qbittorrent/logs:ro \
     --restart unless-stopped \
     mamrenewarr:latest
   ```

2. **API Method**: Uses external IP detection services as fallback

### Configuration File Location

- **Inside Container**: `/app/data/settings.json`
- **On Unraid Host**: `/mnt/user/appdata/MAMRenewARR/settings.json`

You should now see the `settings.json` file appear in your Unraid appdata folder after saving configuration.

## Verification Steps

1. **Check Configuration Persistence**:
   - Go to Config page and save settings
   - Verify `/mnt/user/appdata/MAMRenewARR/settings.json` exists on host
   - Restart container and verify settings are retained

2. **Check IP Detection**:
   - Go to Advanced mode
   - Click "Get IPs"
   - External IP should work (your public IP)
   - VPN IP should either show the VPN IP or fall back to external IP detection

3. **Check Logs**:
   - No more "docker command not found" errors
   - Container should start and run without errors

## Troubleshooting

If VPN IP still shows "Not Found":
1. Ensure your qBittorrent VPN container logs are accessible
2. Update the log path in the Config page to match your setup
3. Consider mounting the qBittorrent log directory as shown above
