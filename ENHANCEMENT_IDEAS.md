# MAMRenewARR Enhancement Ideas

This file contains potential enhancements and feature ideas for the project. Feel free to edit, prioritize, or add your own ideas.

## UI/UX Enhancements

### 1. Version clickable link
Make the version number a clickable link to the GitHub releases page
- **Priority:** Low
- **Effort:** Small
- **Status:** Not Started

### 2. Update checker
API endpoint that checks GitHub for newer releases and shows a notification banner
- **Priority:** Medium
- **Effort:** Medium
- **Status:** Not Started

### 3. Build date/time display
Show when the Docker image was built alongside version number
- **Priority:** Low
- **Effort:** Small
- **Status:** Not Started

### 4. Dark mode toggle button
Add a visible toggle button in the UI (currently users must manually set theme)
- **Priority:** High
- **Effort:** Small
- **Status:** Not Started

### 5. Progress indicators
Real-time progress bars for long operations (session deletion, container restart, etc.)
- **Priority:** Medium
- **Effort:** Medium
- **Status:** Not Started

### 6. Notification system
Toast/popup notifications instead of just inline status messages
- **Priority:** Medium
- **Effort:** Medium
- **Status:** Not Started

## Functionality Enhancements

### 7. Cookie expiration warnings
Alert when session cookies are close to expiring (MAM sessions expire after X days)
- **Priority:** High
- **Effort:** Medium
- **Status:** Not Started

### 8. Health check endpoint
Add `/api/health` endpoint for Docker health checks and external monitoring
- **Priority:** High
- **Effort:** Small
- **Status:** Not Started

### 9. Config validation
Validate settings before saving (URL format, required fields, port numbers, etc.)
- **Priority:** Medium
- **Effort:** Medium
- **Status:** Not Started

### 10. Dry-run mode
Test operations without actually executing them (useful for testing config)
- **Priority:** Low
- **Effort:** Medium
- **Status:** Not Started

### 11. Backup/restore settings
Export/import configuration JSON for easy migration or backup
- **Priority:** Medium
- **Effort:** Small
- **Status:** Not Started

### 12. Multi-container support
Support multiple qBittorrent instances with different VPN IPs
- **Priority:** Low
- **Effort:** Large
- **Status:** Not Started

### 13. Webhook notifications
Send status updates to Discord/Slack/Telegram/etc. when operations complete
- **Priority:** Medium
- **Effort:** Medium
- **Status:** Not Started

## Logging/Monitoring

### 14. Log level UI control
Change log level (Info/Debug) from Config page (backend already supports this)
- **Priority:** Medium
- **Effort:** Small
- **Status:** Not Started

### 15. Real-time log streaming
Live log updates using WebSockets instead of manual refresh button
- **Priority:** Low
- **Effort:** Medium
- **Status:** Not Started

### 16. Statistics dashboard
Track and display success rates, execution times, failure patterns, etc.
- **Priority:** Low
- **Effort:** Large
- **Status:** Not Started

### 17. Session history tracking
Keep detailed history of all session operations with timestamps and outcomes
- **Priority:** Medium
- **Effort:** Medium
- **Status:** Not Started

## Security/Reliability

### 18. API authentication
Protect the web interface with username/password login
- **Priority:** Medium
- **Effort:** Large
- **Status:** Not Started

### 19. Rate limiting
Prevent accidental API spam to MAM (already has some built-in delays)
- **Priority:** Low
- **Effort:** Small
- **Status:** Not Started

### 20. Retry logic configuration
Configure retry attempts and delays in Config page for failed operations
- **Priority:** Low
- **Effort:** Medium
- **Status:** Not Started

### 21. Rollback capability
Undo last operation if something goes wrong (e.g., restore deleted sessions)
- **Priority:** Low
- **Effort:** Large
- **Status:** Not Started

---

## Quick Wins (High Value, Low Effort)
- #4: Dark mode toggle button
- #8: Health check endpoint
- #11: Backup/restore settings
- #14: Log level UI control

## High Priority Items
- #4: Dark mode toggle button
- #7: Cookie expiration warnings
- #8: Health check endpoint

## Notes
Add your own ideas and notes below:

Add prowlarr updating.

Move light/dark mode icon up to header.

More Description of the timer, what does it do? Hover text?

Use Status area at bottom of the screen for something?

Is it using the qbittorrent directory in the config?

Can we make it work with other versions of qbittorrent?

Cleaan up UI, Clean up config, remove unuseeed options, unraid un and pass

Log Handling, Log Colour Coding by severity, Log Clear, log filter, log search.

On basic mode run history, put more info if failed, what failed?

Put the feedback from the push to MAM from qbittorrent CURL command

Move basic mode timer settings to basic mode. Keep config screen for just usernames passwords ip's etc.



