# MAMRenewARR - Updated Deployment Instructions

## Issues Fixed in This Update

1. **Configuration Persistence**: Settings now save to `/app/data/settings.json` which is properly mounted to the Unraid appdata folder
2. **Docker Command Error**: Removed dependency on Docker CLI inside container - no more "docker command not found" errors
3. **VPN IP Detection**: Improved VPN IP detection with multiple fallback methods

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
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  --restart unless-stopped \
  mamrenewarr:latest
```

## Configuration Changes

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
