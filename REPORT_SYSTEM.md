# Crane REST API - Report System Documentation

## Overview
A comprehensive report system has been added to the Crane REST API to track and report on historical container statistics and alert events. The system automatically collects container metrics every 60 seconds and stores alert events when they are triggered by AlertManager.

## Architecture

### Components Implemented

#### 1. Database Models
- **ContainerStats**: Stores real-time container metrics (CPU, memory, network I/O)
  - Fields: app_id, container_name, cpu_percent, memory_usage, memory_limit, memory_percent, net_input, net_output, block_input, block_output, created_at
  
- **AlertHistory**: Logs all alert events
  - Fields: app_id, alert_id, alert_name, status (firing/resolved), severity, summary, description, labels (JSON), timestamps

#### 2. Background Tasks
- **StatsCollector**: Collects container stats every 60 seconds for all active apps
  - Automatically runs on app startup
  - Gracefully stops on app shutdown
  - Configurable collection interval

#### 3. Services
- **report_service.py**: Generates reports from collected data
  - `get_container_stats_report()`: Stats for time ranges
  - `get_alert_history_report()`: Alert events by time range
  - `get_active_alerts()`: Currently firing alerts
  - `get_combined_report()`: Both stats and alerts

#### 4. API Endpoints

All endpoints require JWT authentication (except where noted) and support the following time ranges:
- `1h` - Last 1 hour
- `1d` - Last 1 day (24 hours)
- `1w` - Last 1 week (7 days)
- `1m` - Last 1 month (30 days)

##### Get Container Stats Report
```
GET /api/v1/reports/{app_id}/stats?time_range=1h
```
**Response Example:**
```json
{
  "app_id": 1,
  "time_range": "1h",
  "generated_at": "2024-04-18T10:30:00",
  "data_points": [
    {
      "timestamp": "2024-04-18T10:29:00",
      "container_name": "myapp-1-web",
      "cpu_percent": 2.5,
      "memory_percent": 15.8,
      "memory_usage_mb": 160.5,
      "memory_limit_mb": 1024,
      "net_input_mb": 0.5,
      "net_output_mb": 1.2,
      "block_input_mb": 0.1,
      "block_output_mb": 0.3
    }
  ],
  "summary": {
    "myapp-1-web": {
      "avg_cpu": 2.3,
      "max_cpu": 5.1,
      "min_cpu": 1.2,
      "avg_memory": 15.2,
      "max_memory": 18.5,
      "min_memory": 12.0
    }
  }
}
```

##### Get Alert History Report
```
GET /api/v1/reports/{app_id}/alerts?time_range=1d
```
**Response Example:**
```json
{
  "app_id": 1,
  "time_range": "1d",
  "generated_at": "2024-04-18T10:30:00",
  "alerts": [
    {
      "id": 42,
      "alert_name": "HighCPUUsage",
      "status": "firing",
      "severity": "warning",
      "summary": "CPU usage is above 80%",
      "description": "Container CPU usage exceeded threshold",
      "labels": {
        "job": "myapp-1",
        "instance": "localhost:9090"
      },
      "timestamp": "2024-04-18T09:15:00"
    },
    {
      "id": 43,
      "alert_name": "HighCPUUsage",
      "status": "resolved",
      "severity": "warning",
      "summary": "CPU usage returned to normal",
      "description": "Container CPU usage is now below threshold",
      "labels": {
        "job": "myapp-1",
        "instance": "localhost:9090"
      },
      "timestamp": "2024-04-18T09:45:00"
    }
  ],
  "summary": {
    "total": 2,
    "firing": 1,
    "resolved": 1
  }
}
```

##### Get Active Alerts (Currently Firing)
```
GET /api/v1/reports/{app_id}/alerts/active
```
**Response Example:**
```json
{
  "app_id": 1,
  "active_alerts": [
    {
      "id": 45,
      "alert_name": "HighMemoryUsage",
      "status": "firing",
      "severity": "critical",
      "summary": "Memory usage is critical",
      "description": "Container memory usage exceeded 90%",
      "labels": {
        "job": "myapp-1",
        "instance": "localhost:9090"
      },
      "triggered_at": "2024-04-18T10:15:00"
    }
  ],
  "count": 1
}
```

##### Get Combined Report (Stats + Alerts)
```
GET /api/v1/reports/{app_id}/combined?time_range=1w
```
**Response:**
```json
{
  "app_id": 1,
  "time_range": "1w",
  "generated_at": "2024-04-18T10:30:00",
  "stats": { /* Same as stats endpoint */ },
  "alerts": { /* Same as alerts endpoint */ }
}
```

## Frontend Integration Example

### React Component with Time Range Selector

```javascript
import React, { useState } from 'react';
import axios from 'axios';

const ReportsDashboard = ({ appId }) => {
  const [timeRange, setTimeRange] = useState('1h');
  const [statsReport, setStatsReport] = useState(null);
  const [alertsReport, setAlertsReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchReports = async (range) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token'); // Your JWT token
      const headers = { Authorization: `Bearer ${token}` };

      // Fetch combined report
      const response = await axios.get(
        `/api/v1/reports/${appId}/combined?time_range=${range}`,
        { headers }
      );

      setStatsReport(response.data.stats);
      setAlertsReport(response.data.alerts);
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTimeRangeChange = (newRange) => {
    setTimeRange(newRange);
    fetchReports(newRange);
  };

  return (
    <div className="reports-dashboard">
      <div className="time-range-selector">
        <button 
          onClick={() => handleTimeRangeChange('1h')}
          className={timeRange === '1h' ? 'active' : ''}
        >
          1 Hour
        </button>
        <button 
          onClick={() => handleTimeRangeChange('1d')}
          className={timeRange === '1d' ? 'active' : ''}
        >
          1 Day
        </button>
        <button 
          onClick={() => handleTimeRangeChange('1w')}
          className={timeRange === '1w' ? 'active' : ''}
        >
          1 Week
        </button>
        <button 
          onClick={() => handleTimeRangeChange('1m')}
          className={timeRange === '1m' ? 'active' : ''}
        >
          1 Month
        </button>
      </div>

      {loading && <p>Loading reports...</p>}

      {statsReport && (
        <div className="stats-section">
          <h2>Container Statistics</h2>
          <div className="charts">
            {/* Chart CPU usage over time */}
            {/* Chart Memory usage over time */}
          </div>
          <div className="summary">
            {Object.entries(statsReport.summary).map(([container, stats]) => (
              <div key={container} className="container-summary">
                <h3>{container}</h3>
                <p>Avg CPU: {stats.avg_cpu}%</p>
                <p>Max CPU: {stats.max_cpu}%</p>
                <p>Avg Memory: {stats.avg_memory}%</p>
                <p>Max Memory: {stats.max_memory}%</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {alertsReport && (
        <div className="alerts-section">
          <h2>Alert History</h2>
          <div className="summary">
            <span>Total: {alertsReport.summary.total}</span>
            <span>Firing: {alertsReport.summary.firing}</span>
            <span>Resolved: {alertsReport.summary.resolved}</span>
          </div>
          <div className="alerts-list">
            {alertsReport.alerts.map(alert => (
              <div key={alert.id} className={`alert alert-${alert.status}`}>
                <h4>{alert.alert_name}</h4>
                <p>{alert.summary}</p>
                <p className="timestamp">{alert.timestamp}</p>
                <span className={`severity ${alert.severity}`}>
                  {alert.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportsDashboard;
```

## Data Retention

- **Container Stats**: Retained for 30 days (configurable in `container_stats_crud.delete_old_stats()`)
- **Alert History**: Retained for 90 days (configurable in `alert_history_crud.delete_old_alerts()`)

To modify retention periods, edit the `days` parameter in:
```python
# container_stats_crud.py
ContainerStatsCrud.delete_old_stats(db, days=30)  # Change to desired days

# alert_history_crud.py
AlertHistoryCrud.delete_old_alerts(db, days=90)  # Change to desired days
```

## Configuration

### Stats Collection Interval

The default collection interval is 60 seconds. To change it:

```python
# In background_tasks.py, modify the StatsCollector initialization
stats_collector = StatsCollector(interval_seconds=300)  # 5 minutes
```

## Database Migration

Run the following to create the new tables:

```bash
# The tables will be created automatically on application startup
# via the create_db_and_tables() function in database.py
```

## Troubleshooting

### Background Task Not Running
1. Check logs for startup errors
2. Verify Docker is running
3. Ensure database is accessible

### No Stats Data
1. Verify containers are running
2. Check if background task started (should see log message)
3. Wait at least one collection interval (default 60 seconds)

### Alert History Not Recording
1. Verify AlertManager is sending webhooks to `/api/v1/monitoring/alert`
2. Check that alerts are being triggered in Prometheus
3. Review app logs for alert processing errors

## Performance Considerations

- **Stats Collection**: ~5-50ms per app depending on number of containers
- **Database Queries**: Indexed on app_id and created_at for fast retrieval
- **Storage**: ~100-500 bytes per data point, ~10-50 bytes per alert event

## Future Enhancements

1. Aggregation strategies for large datasets (hourly/daily)
2. Custom retention policies per app
3. Data export (CSV, JSON)
4. Real-time WebSocket updates
5. Custom alert conditions on historical data
6. Performance metrics dashboards
