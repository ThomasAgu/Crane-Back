''' This module contains CRUD operations for alert history '''
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from api.db import models


def create(db: Session, app_id: int, alert_name: str, status: str, 
           alert_id: int = None, severity: str = None, 
           summary: str = None, description: str = None, labels: str = None):
    ''' Create a new alert history record '''
    db_alert_history = models.AlertHistory(
        app_id=app_id,
        alert_id=alert_id,
        alert_name=alert_name,
        status=status,
        severity=severity,
        summary=summary,
        description=description,
        labels=labels
    )
    db.add(db_alert_history)
    db.commit()
    db.refresh(db_alert_history)
    return db_alert_history


def get_alerts_by_time_range(db: Session, app_id: int, hours: int):
    ''' Get alert history for an app within a time range (in hours) '''
    start_time = datetime.now() - timedelta(hours=hours)
    alerts = (
        db.query(models.AlertHistory)
        .filter(
            models.AlertHistory.app_id == app_id,
            models.AlertHistory.created_at >= start_time
        )
        .order_by(desc(models.AlertHistory.created_at))
        .all()
    )
    return alerts


def get_alerts_by_date_range(db: Session, app_id: int, start_date: datetime, end_date: datetime):
    ''' Get alert history for an app within a specific date range '''
    alerts = (
        db.query(models.AlertHistory)
        .filter(
            models.AlertHistory.app_id == app_id,
            models.AlertHistory.created_at >= start_date,
            models.AlertHistory.created_at <= end_date
        )
        .order_by(desc(models.AlertHistory.created_at))
        .all()
    )
    return alerts


def get_alerts_by_status(db: Session, app_id: int, status: str, hours: int):
    ''' Get alert history for an app filtered by status within a time range '''
    start_time = datetime.now() - timedelta(hours=hours)
    alerts = (
        db.query(models.AlertHistory)
        .filter(
            models.AlertHistory.app_id == app_id,
            models.AlertHistory.status == status,
            models.AlertHistory.created_at >= start_time
        )
        .order_by(desc(models.AlertHistory.created_at))
        .all()
    )
    return alerts


def get_active_alerts(db: Session, app_id: int):
    ''' Get currently active (firing) alerts for an app '''
    # Get the latest status for each alert_name
    subquery = (
        db.query(
            models.AlertHistory.alert_name,
            desc(models.AlertHistory.created_at).label('latest_date')
        )
        .filter(models.AlertHistory.app_id == app_id)
        .group_by(models.AlertHistory.alert_name)
        .subquery()
    )
    
    active_alerts = (
        db.query(models.AlertHistory)
        .join(
            subquery,
            (models.AlertHistory.alert_name == subquery.c.alert_name) &
            (models.AlertHistory.created_at == subquery.c.latest_date)
        )
        .filter(
            models.AlertHistory.app_id == app_id,
            models.AlertHistory.status == 'firing'
        )
        .all()
    )
    return active_alerts


def delete_old_alerts(db: Session, days: int = 90):
    ''' Delete alert history older than specified days '''
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count = (
        db.query(models.AlertHistory)
        .filter(models.AlertHistory.created_at < cutoff_date)
        .delete()
    )
    db.commit()
    return deleted_count
