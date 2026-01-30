# Stock Update Background Process Setup

## Overview
Stock data is now stored in the `ItemMaster.item_stock` field and updated via a background process every 5 minutes. This provides:
- ✅ **Fast page loads** (no API calls during page load)
- ✅ **Reliable** (works even if API is temporarily down)
- ✅ **Efficient** (single API call every 5 minutes instead of per-page-load)

## Setup Instructions

### Option 1: Windows Task Scheduler (Recommended for Windows)

1. **Open Task Scheduler** (search "Task Scheduler" in Windows)

2. **Create Basic Task**:
   - Click "Create Basic Task" in the right panel
   - Name: "Update Stock Data"
   - Description: "Updates stock data from API every 5 minutes"

3. **Set Trigger**:
   - Trigger: "Daily" (we'll customize this)
   - Start date: Today
   - Time: Current time
   - Check "Repeat task every: 5 minutes"
   - Duration: "Indefinitely"

4. **Set Action**:
   - Action: "Start a program"
   - Program/script: Full path to `schedule_stock_update.bat`
     - Example: `D:\dataanalyst\Purchase App\schedule_stock_update.bat`
   - Start in: Full path to project directory
     - Example: `D:\dataanalyst\Purchase App`

5. **Save** and the task will run automatically every 5 minutes

### Option 2: Linux/Mac Cron Job

Add this line to your crontab (`crontab -e`):

```bash
*/5 * * * * cd /path/to/Purchase\ App && /path/to/venv/bin/python manage.py import_stock_api >> /path/to/stock_update.log 2>&1
```

### Option 3: Manual Testing

To test the command manually:

```bash
python manage.py import_stock_api
```

## How It Works

1. **Background Process**: Runs `import_stock_api` command every 5 minutes
2. **API Fetch**: Fetches stock data from `https://stock.junaidworld.com/api/stock`
3. **Database Update**: Updates `ItemMaster.item_stock` field for all items
4. **Page Display**: `sales_firm_track` view reads from `ItemMaster.item_stock` (instant, no API call)

## Benefits

- **Performance**: Page loads instantly (no API wait time)
- **Reliability**: Works even if external API is slow/down
- **Efficiency**: One API call every 5 minutes vs. one per page load
- **Scalability**: No impact on page load time regardless of traffic

## Monitoring

Check the Task Scheduler history or log files to ensure the task is running successfully.
