# Alert Service Fix: Database to Prometheus Sync

## Problem
Custom alerts saved in the database were not appearing in Prometheus, even though static alerts defined in YAML files (`rules.yml` and `app_1.yml`) were working correctly.

## Root Cause
Prometheus only reads alert rules from YAML files in the `./api/files/monitoring/rules/` directory. The custom alerts were being saved to the database but never converted to YAML format, so Prometheus had no way to know about them.

## Solution
Implemented a syncing mechanism that:

1. **Generates Prometheus-compatible YAML rules** from database custom alerts
2. **Writes them to a file** (`custom_alerts.yml`) in the rules directory where Prometheus reads from
3. **Reloads Prometheus** to pick up the new rules immediately

## Changes Made

### 1. New Service: `api/services/prometheus_sync_service.py`
- `generate_prometheus_rules()`: Converts database CustomAlert objects to Prometheus YAML format
- `sync_alerts_to_prometheus()`: Fetches all alerts from DB and writes to `custom_alerts.yml`
- `trigger_prometheus_reload()`: Calls Prometheus API to reload rules (requires `--web.enable-lifecycle` flag)

### 2. Updated: `api/services/alert_service.py`
- Imports the new sync service
- Calls `sync_alerts_to_prometheus()` and `trigger_prometheus_reload()` after:
  - Creating a new alert
  - Updating an existing alert
  - Deleting an alert

### 3. Updated: `api/files/monitoring/docker-compose.yml`
- Added `--web.enable-lifecycle` flag to Prometheus command
- This allows Prometheus to reload rules dynamically via the reload endpoint

### 4. Updated: `main.py`
- Added initial sync call during application startup
- Ensures all existing custom alerts are synced to rules file on app start

## How It Works

### On Alert Creation
```
User creates alert via API
  ↓
Alert saved to database
  ↓
sync_alerts_to_prometheus() called
  ↓
All DB alerts converted to YAML format
  ↓
Written to ./api/files/monitoring/rules/custom_alerts.yml
  ↓
trigger_prometheus_reload() called
  ↓
Prometheus reloads rules from file
  ↓
New alerts now active in Prometheus ✓
```

### Generated YAML Format
```yaml
groups:
- name: custom-alerts
  rules:
  - alert: my_custom_alert
    expr: up == 0
    for: 5m
    labels:
      severity: critical
      app_id: '1'
      job: my-app
    annotations:
      summary: "Alert triggered for my-app"
      description: "Service is down"
```

## Testing the Fix

1. **Verify Prometheus is running** with the updated docker-compose:
   ```bash
   docker-compose -f api/files/monitoring/docker-compose.yml up -d
   ```

2. **Restart your FastAPI application** to sync existing alerts:
   ```bash
   uvicorn main:app --reload
   ```

3. **Create a new custom alert** via the API:
   ```bash
   POST /api/v1/alert/{app_id}
   {
     "alert": "test_alert",
     "expr": "up == 0",
     "for_time": "5m",
     "severity": "warning",
     "summary": "Test alert",
     "description": "This is a test alert"
   }
   ```

4. **Check Prometheus**:
   - Go to `http://localhost:9090`
   - Alerts tab should show your custom alert
   - Check `/etc/prometheus/rules/custom_alerts.yml` file (inside container)

## Files Modified
- `api/services/prometheus_sync_service.py` (NEW)
- `api/services/alert_service.py`
- `api/files/monitoring/docker-compose.yml`
- `main.py`

## Notes
- The sync service runs synchronously but is fast for most deployments
- If many alerts exist, consider making this async in future optimization
- Prometheus will pick up new rules within its evaluation interval (default 5s)
- The `custom_alerts.yml` file is auto-generated - don't edit it manually
