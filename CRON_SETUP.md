# Cron Job Setup for Stock Update on VPS

## Quick Setup

### Step 1: Create the Shell Script

1. Copy `schedule_stock_update.sh` to your VPS
2. Edit the script and update these paths:
   ```bash
   PROJECT_DIR="/path/to/Purchase App"  # Change to your actual project path
   VENV_PATH="/path/to/Purchase App/venv"  # Change to your actual venv path
   ```

3. Make it executable:
   ```bash
   chmod +x schedule_stock_update.sh
   ```

### Step 2: Test the Script Manually

Test that the script works:
```bash
./schedule_stock_update.sh
```

### Step 3: Set Up Cron Job

1. **Open crontab editor:**
   ```bash
   crontab -e
   ```

2. **Add this line to run every 5 minutes:**
   ```bash
   */5 * * * * /full/path/to/schedule_stock_update.sh >> /var/log/stock_update.log 2>&1
   ```

   **Or with better logging (recommended):**
   ```bash
   */5 * * * * /var/www/purchase-track/schedule_stock_update.sh >> /var/log/purchase_stock_update.log 2>&1 || echo "$(date): Stock update failed" >> /var/log/stock_update_errors.log
   ```

3. **Save and exit** (in vi: press `Esc`, type `:wq`, press Enter)

### Step 4: Verify Cron Job

1. **List your cron jobs:**
   ```bash
   crontab -l
   ```

2. **Check if cron service is running:**
   ```bash
   systemctl status cron
   # or
   systemctl status crond
   ```

3. **View logs to verify it's working:**
   ```bash
   tail -f /var/log/stock_update.log
   ```

## Alternative: Direct Cron Command (Without Script)

If you prefer to run the command directly in cron:

```bash
*/5 * * * * cd /path/to/Purchase\ App && /path/to/venv/bin/python manage.py import_stock_api >> /var/log/stock_update.log 2>&1
```

**Note:** Use `\ ` (backslash space) to escape spaces in paths.

## Cron Schedule Format

```
*/5 * * * *  = Every 5 minutes
0 * * * *    = Every hour
0 */2 * * *  = Every 2 hours
0 0 * * *    = Daily at midnight
```

## Troubleshooting

### Check if cron is running:
```bash
systemctl status cron
# or
ps aux | grep cron
```

### View cron execution logs:
```bash
# On Ubuntu/Debian:
grep CRON /var/log/syslog

# On CentOS/RHEL:
grep CRON /var/log/cron
```

### Test with a simple cron job first:
```bash
* * * * * echo "Test $(date)" >> /tmp/cron_test.log
```

### Common Issues:

1. **Path issues**: Always use full absolute paths in cron
2. **Permissions**: Make sure the script is executable (`chmod +x`)
3. **Environment**: Cron runs with minimal environment variables. If you need specific env vars, add them to the script
4. **Python path**: Make sure the virtual environment Python is used

## Logging Locations

- Success/Output: `/var/log/stock_update.log`
- Errors: `/var/log/stock_update_errors.log` (if using the recommended version)

You can change these paths to any location you have write permissions to.
