''' This module contains the routes for alert routes'''
from fastapi import APIRouter, Depends
from api.routes.auth_routes import verify_jwt
from sqlalchemy.orm import Session
from api.db.database import get_db
import api.services.alert_service as AlertService
from api.schemas.alert import CustomAlert as CustomAlertSchema

alertRouter = APIRouter()

@alertRouter.get("/{app_id}", tags=["Alert"], description="Get custom alerts given an app_id", response_model_exclude_none=True, dependencies=[Depends(verify_jwt)])
async def get_alerts_by_app_id(app_id: int, db: Session = Depends(get_db)):
  return await AlertService.get_alerts(db, app_id)

@alertRouter.post("/{app_id}", tags=["Alert"], description="create a custom_alert for an app_id", response_model_exclude_none=True)
async def create_alert(app_id: int, alert: CustomAlertSchema, db: Session = Depends(get_db)):
  return await AlertService.create(db, app_id, alert)

@alertRouter.patch("/{app_id}/alert/{alert_id}", tags=['Alert'], description="update a custom_alert for an app_id", response_model_exclude_none=True, dependencies=[Depends(verify_jwt)])
async def update_alert(app_id: int, alert_id: int, alert: CustomAlertSchema, db: Session = Depends(get_db)):
  return await AlertService.update(db, app_id, alert, alert_id)

@alertRouter.delete("/{app_id}/alert/{alert_id}", tags=["Alert"], description="Delete a custom alert for an app and regenerate")
async def delete_alert(app_id: int, alert_id: int, db: Session = Depends(get_db)):
  return await AlertService.delete(db, app_id, alert_id)