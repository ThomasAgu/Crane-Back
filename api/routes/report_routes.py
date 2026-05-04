''' This module contains the routes for reporting '''
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.routes.auth_routes import verify_jwt
import api.services.report_service as ReportService

reportRouter = APIRouter()


@reportRouter.get("/{app_id}/stats", tags=["Reports"], 
                  description="Get historical container stats for an app",
                  response_model_exclude_none=True, 
                  dependencies=[Depends(verify_jwt)])
async def get_stats_report(
    app_id: int,
    time_range: str = Query('1h', regex='^(1h|1d|1w|1m)$'),
    db: Session = Depends(get_db)
):
    """
    Get container statistics report for an app.
    
    Query Parameters:
    - time_range: '1h' (1 hour), '1d' (1 day), '1w' (1 week), '1m' (1 month)
    
    Returns aggregated stats (avg, min, max) and detailed data points.
    """
    return await ReportService.get_container_stats_report(db, app_id, time_range)


@reportRouter.get("/{app_id}/alerts", tags=["Reports"],
                  description="Get alert history for an app",
                  response_model_exclude_none=True,
                  dependencies=[Depends(verify_jwt)])
async def get_alerts_report(
    app_id: int,
    time_range: str = Query('1h', regex='^(1h|1d|1w|1m)$'),
    db: Session = Depends(get_db)
):
    """
    Get alert history report for an app.
    
    Query Parameters:
    - time_range: '1h' (1 hour), '1d' (1 day), '1w' (1 week), '1m' (1 month)
    
    Returns list of triggered alerts with status and summary.
    """
    return await ReportService.get_alert_history_report(db, app_id, time_range)


@reportRouter.get("/{app_id}/alerts/active", tags=["Reports"],
                  description="Get currently active alerts for an app",
                  response_model_exclude_none=True,
                  dependencies=[Depends(verify_jwt)])
async def get_active_alerts(
    app_id: int,
    db: Session = Depends(get_db)
):
    """
    Get currently active (firing) alerts for an app.
    
    Returns only alerts with 'firing' status.
    """
    return await ReportService.get_active_alerts(db, app_id)


@reportRouter.get("/{app_id}/combined", tags=["Reports"],
                  description="Get combined stats and alerts report",
                  response_model_exclude_none=True,
                  dependencies=[Depends(verify_jwt)])
async def get_combined_report(
    app_id: int,
    time_range: str = Query('1h', regex='^(1h|1d|1w|1m)$'),
    db: Session = Depends(get_db)
):
    """
    Get a combined report with both container stats and alert history.
    
    Query Parameters:
    - time_range: '1h' (1 hour), '1d' (1 day), '1w' (1 week), '1m' (1 month)
    
    Returns both stats and alerts in a single response.
    """
    return await ReportService.get_combined_report(db, app_id, time_range)
