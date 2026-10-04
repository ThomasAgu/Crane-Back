''' This module contains CRUD operations for container stats '''
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Float
from api.db import models


def create(db: Session, app_id: int, container_stats):
    ''' Create a new container stats record '''
    # Handle both dictionary and object attributes
    def get_value(obj, key, default=''):
        if isinstance(obj, dict):
            return str(obj.get(key, default))
        else:
            return str(getattr(obj, key, default))
    
    db_stats = models.ContainerStats(
        app_id=app_id,
        container=get_value(container_stats, 'container', ''),
        container_id=get_value(container_stats, 'container_id', ''),
        container_name=get_value(container_stats, 'container_name', ''),
        cpu_percentage=get_value(container_stats, 'cpu_percentage', '0'),
        memory_used=get_value(container_stats, 'memory_used', '0'),
        memory_limit=get_value(container_stats, 'memory_limit', '0'),
        memory_percentage=get_value(container_stats, 'memory_percentage', '0'),
        net_upload=get_value(container_stats, 'net_upload', '0'),
        net_download=get_value(container_stats, 'net_download', '0'),
        block_read=get_value(container_stats, 'block_read', '0'),
        block_write=get_value(container_stats, 'block_write', '0')
    )
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    return db_stats


def get_stats_by_time_range(db: Session, app_id: int, hours: int):
    ''' Get container stats for an app within a time range (in hours) '''
    start_time = datetime.now() - timedelta(hours=hours)
    stats = (
        db.query(models.ContainerStats)
        .filter(
            models.ContainerStats.app_id == app_id,
            models.ContainerStats.created_at >= start_time
        )
        .order_by(desc(models.ContainerStats.created_at))
        .all()
    )
    return stats


def get_stats_by_date_range(db: Session, app_id: int, start_date: datetime, end_date: datetime):
    ''' Get container stats for an app within a specific date range '''
    stats = (
        db.query(models.ContainerStats)
        .filter(
            models.ContainerStats.app_id == app_id,
            models.ContainerStats.created_at >= start_date,
            models.ContainerStats.created_at <= end_date
        )
        .order_by(desc(models.ContainerStats.created_at))
        .all()
    )
    return stats


def get_aggregated_stats_by_container(db: Session, app_id: int, hours: int):
    ''' Get aggregated container stats (avg, min, max) for an app '''
    start_time = datetime.now() - timedelta(hours=hours)
    
    aggregated = (
        db.query(
            models.ContainerStats.container_name,
            func.avg(cast(models.ContainerStats.cpu_percentage, Float)).label('avg_cpu'),
            func.max(cast(models.ContainerStats.cpu_percentage, Float)).label('max_cpu'),
            func.min(cast(models.ContainerStats.cpu_percentage, Float)).label('min_cpu'),
            func.avg(cast(models.ContainerStats.memory_percentage, Float)).label('avg_memory'),
            func.max(cast(models.ContainerStats.memory_percentage, Float)).label('max_memory'),
            func.min(cast(models.ContainerStats.memory_percentage, Float)).label('min_memory'),
        )
        .filter(
            models.ContainerStats.app_id == app_id,
            models.ContainerStats.created_at >= start_time
        )
        .group_by(models.ContainerStats.container_name)
        .all()
    )
    return aggregated


def delete_old_stats(db: Session, days: int = 30):
    ''' Delete container stats older than specified days '''
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count = (
        db.query(models.ContainerStats)
        .filter(models.ContainerStats.created_at < cutoff_date)
        .delete()
    )
    db.commit()
    return deleted_count
