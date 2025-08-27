# MyAnonamouseRenewARR Project Summary

_Last updated: 2025-07-31_

## Features Implemented
- **Get IPs button** in Advanced Mode: Fetches external IP (via public API) and VPN IP (from qBittorrentVPN container log file).
- **Config page**: Lets user set qBittorrentVPN container name and log file path; settings are persisted in `settings.json`.
- **Dockerized Flask app**: Runs cross-platform (Windows, Unraid, MacOS), uses Waitress for production serving.
- **Frontend/Backend integration**: AJAX config save/load, Get IPs result display.
- **.gitignore**: Protects sensitive files like `settings.json`.

## How to Deploy on Unraid
1. Clone repo from GitHub.
2. Build Docker image:
   ```sh
   docker build -t mamrenewarr:test .
   ```
3. (Optional) Create settings file for persistence:
   ```sh
   mkdir -p /mnt/user/appdata/MAMRenewARR
   touch /mnt/user/appdata/MAMRenewARR/settings.json
   ```
4. Run container:
   ```sh
   docker run -d --name mamrenewarr-test -p 5000:5000 -v /mnt/user/appdata/MAMRenewARR/settings.json:/app/settings.json mamrenewarr:test
   ```
5. Visit `http://<unraid-ip>:5000` in your browser.

## Outstanding Tasks
- [ ] Further hardening of error handling (if needed)
- [ ] UI/UX polish as desired
- [ ] Add more features as required

## Notes
- The "Get IPs" feature requires the app to be running on the same host as the qBittorrentVPN container (e.g., Unraid).
- All config is persisted in `settings.json` (not tracked by git).
- For any AI or Windsurf context, paste this summary after reinstall for instant project recall.
