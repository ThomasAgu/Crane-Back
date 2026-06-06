'''
This module defines the NotificationService class, which provides methods for sending notifications to users.
'''
import api.db.crud.notification_crud as NotificationCrud

async def get_notifications_by_user_id(db, user_id: int):
    ''' Get notifications for a user by ID '''
    notifications = NotificationCrud.get_by_user_id(db, user_id)
    return notifications

async def create_notification(db, user_id: int, message: str):
    ''' Create a new notification for a user '''
    notification = NotificationCrud.create(db, user_id, message)
    return notification

async def delete_notification(db, notification_id: int):
    ''' Delete a notification by ID '''
    notification = NotificationCrud.delete(db, notification_id)
    return notification

async def mark_notification_as_read(db, notification_id: int):
    ''' Mark a notification as read by ID '''
    notification = NotificationCrud.mark_as_read(db, notification_id)
    return notification

async def mark_all_notifications_as_read(db, user_id: int):
    ''' Mark all notifications as read for a user by ID '''
    notifications = NotificationCrud.mark_all_as_read(db, user_id)
    return notifications

