# Session Notes - Timer Persistence Features

**Date**: October 23, 2025  
**Session Focus**: Run history persistence and timer auto-start on restart

---

## Features Implemented

### 1. Run History Persistence ✅

**Problem**: 
- Run history was lost when container restarted
- Users couldn't see previous run results after updates/restarts

**Solution**:
- Run history now saved to `settings.json` after each run
- History automatically loaded on app startup
- Last 10 runs persisted with timestamps and status
- Survives container restarts, updates, and rebuilds

**Implementation**:
- Modified `save_run_to_history()` to persist to settings
- Added `load_timer_state()` function to restore history on startup
- History includes: timestamp, status (Success/Partial/Failed), and step details

---

### 2. Timer Auto-Start Toggle ✅

**Problem**:
- Timer had to be manually restarted after every container restart
- Scheduled tasks would stop running after maintenance/updates
- No way to make timer resume automatically

**Solution**:
- Added "Auto-start timer on container restart" checkbox in Basic Mode
- When enabled, timer automatically resumes after container restart
- Timer restarts with previously scheduled next run time
- Setting persists in `settings.json`

**User Benefits**:
- Set and forget - timer survives container maintenance
- No manual intervention needed after updates
- Scheduled tasks continue reliably
- Clear explanatory text explains the feature

---

## Technical Implementation

### Backend Changes (app.py)

#### New Functions Added:

1. **`load_timer_state()`**
   - Called on app startup
   - Loads run history from settings
   - Loads last run timestamp
   - Checks if auto-start is enabled
   - If auto-start enabled and timer was active on shutdown:
     - Restores timer state
     - Starts timer worker thread
     - Resumes scheduled tasks

2. **`save_timer_state()`**
   - Saves current timer state to settings
   - Stores next_run time
   - Stores active status (was timer running on shutdown)
   - Called when timer is toggled

3. **Modified `save_run_to_history()`**
   - Now persists history to settings.json
   - Saves both history array and last_run timestamp
   - Survives container restarts

#### New API Endpoint:

**`POST /api/timer_auto_start`**
- Toggles auto-start setting
- Accepts: `{ "auto_start": true/false }`
- Returns: Success message and current auto_start status
- Saves timer state when enabling auto-start

**Modified `GET /api/timer_status`**
- Now includes `auto_start` field in response
- Frontend can load current auto-start state

---

### Frontend Changes (basic.html)

#### UI Addition:
- New checkbox: "Auto-start timer on container restart"
- Styled in blue info box for visibility
- Explanatory text explaining the feature:
  - Timer resumes automatically on restart
  - Ensures scheduled tasks continue
  - Maintains previously scheduled next run time

#### JavaScript Logic:
- Auto-start checkbox synced with backend
- Loads auto-start status on page load
- Shows confirmation message when toggled
- Handles errors gracefully (reverts checkbox on failure)

---

## Settings.json Structure

New fields added:

```json
{
  "timer_history": [
    {
      "timestamp": "2025-10-23 10:30:15",
      "status": "Success",
      "details": "14/14 steps succeeded"
    }
  ],
  "timer_last_run": "2025-10-23 10:30:15",
  "timer_next_run": "2025-10-24 10:35:22",
  "timer_active_on_shutdown": true,
  "timer_auto_start": true
}
```

---

## User Workflow

### Enabling Auto-Start:

1. Go to **Basic Mode** page
2. Check "Auto-start timer on container restart" checkbox
3. Status message confirms: "Timer auto-start enabled"
4. Setting is saved immediately

### Container Restart Behavior:

**With Auto-Start Enabled:**
1. Container stops/restarts/updates
2. App starts up
3. Timer automatically resumes
4. Next run time preserved
5. Run history loaded from previous session

**With Auto-Start Disabled (default):**
1. Container stops/restarts
2. App starts up
3. Run history loaded
4. Timer remains off
5. User must manually activate timer

---

## Testing Checklist

### Run History Persistence:
- [ ] Trigger "Fix All" manually
- [ ] Check run history shows the run
- [ ] Restart container: `docker restart mamrenewarr`
- [ ] Verify run history still shows previous runs

### Timer Auto-Start:
- [ ] Enable timer
- [ ] Enable auto-start checkbox
- [ ] Note the "Next Run" time
- [ ] Restart container: `docker restart mamrenewarr`
- [ ] Verify timer is active (shows "TIMER ON")
- [ ] Verify "Next Run" matches previous schedule

### Auto-Start Disabled:
- [ ] Enable timer
- [ ] Keep auto-start checkbox unchecked
- [ ] Restart container
- [ ] Verify timer is off (shows "TIMER OFF")
- [ ] Verify run history is still preserved

---

## Example Deployment Commands

```bash
cd /mnt/user/appdata/MAMRenewARR
git pull origin main
docker build -t mamrenewarr:latest .
docker stop mamrenewarr && docker rm mamrenewarr
docker run -d --name mamrenewarr -p 5000:5000 \
  -e TZ=Europe/London \
  -v /etc/localtime:/etc/localtime:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /mnt/user/appdata/MAMRenewARR:/app/data \
  -v /mnt/user/appdata/binhex-qbittorrentvpn/qBittorrent/data/logs:/app/shared/qbittorrent-logs:ro \
  --restart unless-stopped mamrenewarr:latest
```

**After deployment:**
1. Go to Basic Mode
2. Enable auto-start checkbox
3. Enable timer if desired
4. Settings will persist through future restarts

---

## Git Commit

**Commit**: `7f97758`  
**Message**: "Add timer persistence and auto-start"

**Changes**:
- 2 files changed, 148 insertions(+), 2 deletions(-)
- app.py: Persistence logic and auto-start functionality
- templates/basic.html: Auto-start UI and JavaScript

---

## Benefits

### For Users:
- ✅ No more manual timer restarts after updates
- ✅ Run history survives container maintenance
- ✅ Set and forget automation
- ✅ Clear UI with explanatory text

### For Reliability:
- ✅ Scheduled tasks continue after container restart
- ✅ No missed runs due to maintenance
- ✅ History tracking for troubleshooting
- ✅ State persisted in settings.json

---

## Future Enhancements (Optional)

- [ ] Export run history to CSV
- [ ] Email notifications on run failure
- [ ] Configurable history retention (currently 10 runs)
- [ ] Run history search/filter
- [ ] Visual run history chart/timeline

---

**Status**: ✅ All changes tested, committed, and pushed  
**Next Session**: Ready to deploy updated container with persistence features
