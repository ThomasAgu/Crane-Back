from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.routes.auth_routes import verify_jwt
import api.services.notification_service as NotificationService

notificationRouter = APIRouter()

@notificationRouter.get("/", tags=["Notifications"], description="Get all notifications for the authenticated user", response_model_exclude_none=True)
async def get_notifications(db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    notifications = await NotificationService.get_notifications_by_user_id(db, db_user.id)
    return notifications

@notificationRouter.delete('/{notification_id}', tags=["Notifications"], description="Delete a notification by ID")
async def delete_notification(notification_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
  notification = await NotificationService.delete_notification(db, notification_id)
  if not notification:
    raise HTTPException(status_code=404, detail="Notification not found")
  return {"detail": "Notification deleted successfully"}

@notificationRouter.post("/{notification_id}/read", tags=["Notifications"], description="Mark a notification as read by ID")
async def mark_notification_as_read(notification_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
  notification = await NotificationService.mark_notification_as_read(db, notification_id)
  if not notification:
    raise HTTPException(status_code=404, detail="Notification not found")
  return {"detail": "Notification marked as read successfully"}

@notificationRouter.post("/read-all", tags=["Notifications"], description="Mark all notifications as read for the authenticated user")
async def mark_all_notifications_as_read(db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
  notifications = await NotificationService.mark_all_notifications_as_read(db, db_user.id)
  return {"detail": "All notifications marked as read successfully", "notifications": notifications}