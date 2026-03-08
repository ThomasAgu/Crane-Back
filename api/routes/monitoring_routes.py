''' This module contains the routes for monitoring the application '''
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import api.services.monitoring_service as MonitoringService
from api.db.database import get_db
from api.routes.auth_routes import verify_jwt
from api.services.alert_service import manage_alert

monitoringRouter = APIRouter()

@monitoringRouter.post("/", tags=["Monitoring"], description="Start Prometheus and Alert Manager services", response_model_exclude_none=True, dependencies=[Depends(verify_jwt)])
async def start():
    return await MonitoringService.start_monitoring()


@monitoringRouter.post("/stop", tags=["Monitoring"], description="Stop Prometheus and Alert Manager services", response_model_exclude_none=True, dependencies=[Depends(verify_jwt)])
async def stop():
    return await MonitoringService.stop_monitoring()


@monitoringRouter.post("/restart", tags=["Monitoring"], description="Restart Prometheus and Alert Manager services", response_model_exclude_none=True, dependencies=[Depends(verify_jwt)])
async def restart():
    return await MonitoringService.restart_monitoring()

@monitoringRouter.post("/alert", tags=["Monitoring"], description="Receive Alert Manager Webhook notification")
async def alert(data: Dict[Any, Any], db: Session = Depends(get_db)):
    return await manage_alert(db, data)
