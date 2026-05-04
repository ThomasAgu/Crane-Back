# Report System - Quick Start Guide

## What Was Added?

A complete **historical reporting system** for container statistics and alert tracking in the Crane REST API.

## Key Features

### 1. **Automatic Stats Collection**
- Container metrics collected every 60 seconds
- Metrics: CPU %, Memory %, Network I/O, Block I/O
- Stored in PostgreSQL database
- Fully automated background task

### 2. **Alert History Tracking**
- Every alert from AlertManager is logged
- Tracks: alert name, status (firing/resolved), severity, timestamps
- Linked to your CustomAlert rules
- Query by time range and status

### 3. **Time-Based Reports**
Four time range options:
- **1h** - Last 1 hour
- **1d** - Last 1 day
- **1w** - Last 1 week
- **1m** - Last 1 month

### 4. **API Endpoints**
All endpoints at `/api/v1/reports/`:
```
GET  /api/v1/reports/{app_id}/stats        - Container stats for time range
GET  /api/v1/reports/{app_id}/alerts       - Alert history for time range
GET  /api/v1/reports/{app_id}/alerts/active - Currently firing alerts
GET  /api/v1/reports/{app_id}/combined     - Both stats + alerts
```

## Files Added/Modified

### New Files Created
1. **api/services/report_service.py** - Report generation logic
2. **api/services/background_tasks.py** - Stats collection background task
3. **api/routes/report_routes.py** - API endpoints
4. **api/db/crud/container_stats_crud.py** - Stats database operations
5. **api/db/crud/alert_history_crud.py** - Alert history database operations
6. **api/schemas/report.py** - Response schemas for reports
7. **REPORT_SYSTEM.md** - Full documentation

### Files Modified
1. **api/db/models.py** - Added ContainerStats and AlertHistory models
2. **api/services/alert_service.py** - Updated to log alerts to history
3. **main.py** - Registered report routes, started background tasks

## Usage Example

### Get Stats for Last Hour
```bash
curl -X GET "http://localhost:8000/api/v1/reports/1/stats?time_range=1h" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response
```json
{
  "app_id": 1,
  "time_range": "1h",
  "data_points": [...],
  "summary": {
    "container-name": {
      "avg_cpu": 2.5,
      "max_cpu": 5.0,
      "min_cpu": 1.0,
      "avg_memory": 15.0,
      "max_memory": 20.0,
      "min_memory": 10.0
    }
  }
}
```

### Get Active Alerts
```bash
curl -X GET "http://localhost:8000/api/v1/reports/1/alerts/active" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Combined Report
```bash
curl -X GET "http://localhost:8000/api/v1/reports/1/combined?time_range=1d" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Frontend Implementation

### Time Range Selector
```javascript
const timeRanges = ['1h', '1d', '1w', '1m'];

<select onChange={(e) => fetchReport(e.target.value)}>
  <option value="1h">Last Hour</option>
  <option value="1d">Last Day</option>
  <option value="1w">Last Week</option>
  <option value="1m">Last Month</option>
</select>
```

### Fetch Combined Report
```javascript
const fetchReport = async (timeRange) => {
  const response = await fetch(
    `/api/v1/reports/${appId}/combined?time_range=${timeRange}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  const data = await response.json();
  
  // data.stats has container statistics
  // data.alerts has alert history
};
```

## Starting the Application

The report system automatically starts when the application starts:

```bash
# Simply run your app as usual
uvicorn main:app --reload

# You'll see in logs:
# "Stats collector started with 60s interval"
```

## Configuration Options

### Change Stats Collection Interval
In `api/services/background_tasks.py`:
```python
# Default is 60 seconds
stats_collector = StatsCollector(interval_seconds=60)

# Change to 300 seconds (5 minutes)
stats_collector = StatsCollector(interval_seconds=300)
```

### Change Data Retention
In `api/db/crud/container_stats_crud.py`:
```python
# Default is 30 days
ContainerStatsCrud.delete_old_stats(db, days=30)
```

In `api/db/crud/alert_history_crud.py`:
```python
# Default is 90 days
AlertHistoryCrud.delete_old_alerts(db, days=90)
```

## Data Storage

- **Container Stats**: 1 record per container per collection interval
  - Default: 1440 records/day per container (60-second intervals)
  - Stored for 30 days
  
- **Alert History**: 1 record per alert event
  - Stored for 90 days
  - Includes all metadata from AlertManager

## Next Steps

1. **Start your API**: `uvicorn main:app --reload`
2. **Frontend**: Update your dashboard to use the new endpoints
3. **Test**: Use the example curl commands above
4. **Monitor**: Watch for "Stats collector started" in logs
5. **Review**: Check REPORT_SYSTEM.md for detailed documentation

## Troubleshooting

### Stats not being collected?
1. Wait 60+ seconds after startup
2. Ensure containers are running
3. Check logs for errors

### Alerts not in history?
1. Verify AlertManager webhook is configured
2. Check that alerts are firing in Prometheus
3. Make sure CustomAlerts are properly configured

### Empty reports?
1. Ensure time range has passed since app startup
2. Check logs for collection errors
3. Verify app_id is correct

## Support

- See [REPORT_SYSTEM.md](./REPORT_SYSTEM.md) for full API documentation
- Check logs for diagnostic information
- Review background_tasks.py for implementation details
