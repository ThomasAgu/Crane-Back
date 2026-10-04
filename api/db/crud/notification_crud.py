from sqlalchemy.orm import Session
from api.db import models, schemas

def get_by_user_id(db: Session, user_id: int):
    ''' Get notifications by user ID '''
    return db.query(models.Notification).filter(models.Notification.user_id == user_id).all()

def create(db: Session, notification: schemas.NotificationCreate):
    ''' Create a new notification '''
    
    # Mapeas a mano cada campo del esquema al modelo de SQLAlchemy
    db_notification = models.Notification(
        user_id=notification.user_id,
        name=notification.name,
        description=notification.description
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def delete(db: Session, notification_id: int):
    ''' Delete a notification by ID '''
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if notification:
        db.delete(notification)
        db.commit()
    return notification

def get_unread_by_user_id(db: Session, user_id: int):
    ''' Get unread notifications by user ID '''
    return db.query(models.Notification).filter(models.Notification.user_id == user_id, models.Notification.read_by_user == False).all()

def mark_as_read(db: Session, notification_id: int):
    ''' Mark a notification as read by ID '''
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if notification:
        notification.read_by_user = True
        db.commit()
    return notification

def mark_all_as_read(db: Session, user_id: int):
    ''' Mark all notifications as read for a user by ID '''
    db.query(models.Notification).filter(models.Notification.user_id == user_id).update({models.Notification.read_by_user: True})
    db.commit()
    return db.query(models.Notification).filter(models.Notification.user_id == user_id).all()