''' This module contains services for managing reports '''
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import api.db.crud.container_stats_crud as ContainerStatsCrud
import api.db.crud.alert_history_crud as AlertHistoryCrud
from api.db import models
import json


TIME_RANGES = {
    '1h': 1,
    '1d': 24,
    '1w': 24 * 7,
    '1m': 24 * 30
}


async def get_container_stats_report(db: Session, app_id: int, time_range: str = '1h'):
    ''' 
    Get container stats report for an app within a time range
    time_range: '1h', '1d', '1w', '1m'
    '''
    hours = TIME_RANGES.get(time_range, 1)
    stats = ContainerStatsCrud.get_stats_by_time_range(db, app_id, hours)
    
    if not stats:
        return {
            'app_id': app_id,
            'time_range': time_range,
            'data_points': [],
            'summary': None
        }
    
    # Get aggregated stats
    aggregated = ContainerStatsCrud.get_aggregated_stats_by_container(db, app_id, hours)
    
    # Format data for frontend
    data_points = []
    for stat in stats:
        data_points.append({
            'timestamp': stat.created_at.isoformat(),
            'container': stat.container,
            'container_id': stat.container_id,
            'container_name': stat.container_name,
            'cpu_percentage': float(stat.cpu_percentage),
            'memory_percentage': float(stat.memory_percentage),
            'memory_used_mb': round(float(stat.memory_used) / (1024 * 1024), 2),
            'memory_limit_mb': round(float(stat.memory_limit) / (1024 * 1024), 2),
            'net_upload_mb': round(float(stat.net_upload) / (1024 * 1024), 2),
            'net_download_mb': round(float(stat.net_download) / (1024 * 1024), 2),
            'block_read_mb': round(float(stat.block_read) / (1024 * 1024), 2),
            'block_write_mb': round(float(stat.block_write) / (1024 * 1024), 2),
        })
    
    # Build summary
    summary = {}
    for agg in aggregated:
        summary[agg.container_name] = {
            'avg_cpu': round(float(agg.avg_cpu) if agg.avg_cpu else 0, 2),
            'max_cpu': round(float(agg.max_cpu) if agg.max_cpu else 0, 2),
            'min_cpu': round(float(agg.min_cpu) if agg.min_cpu else 0, 2),
            'avg_memory': round(float(agg.avg_memory) if agg.avg_memory else 0, 2),
            'max_memory': round(float(agg.max_memory) if agg.max_memory else 0, 2),
            'min_memory': round(float(agg.min_memory) if agg.min_memory else 0, 2),
        }
    
    return {
        'app_id': app_id,
        'time_range': time_range,
        'generated_at': datetime.now().isoformat(),
        'data_points': data_points,
        'summary': summary
    }


async def get_alert_history_report(db: Session, app_id: int, time_range: str = '1h'):
    ''' 
    Get alert history report for an app within a time range
    time_range: '1h', '1d', '1w', '1m'
    '''
    hours = TIME_RANGES.get(time_range, 1)
    alerts = AlertHistoryCrud.get_alerts_by_time_range(db, app_id, hours)
    
    if not alerts:
        return {
            'app_id': app_id,
            'time_range': time_range,
            'alerts': [],
            'summary': {
                'total': 0,
                'firing': 0,
                'resolved': 0
            }
        }
    
    # Format alerts for frontend
    formatted_alerts = []
    firing_count = 0
    resolved_count = 0
    
    for alert in alerts:
        formatted_alerts.append({
            'id': alert.id,
            'alert_name': alert.alert_name,
            'status': alert.status,
            'severity': alert.severity,
            'summary': alert.summary,
            'description': alert.description,
            'labels': json.loads(alert.labels) if alert.labels else {},
            'timestamp': alert.created_at.isoformat()
        })
        
        if alert.status == 'firing':
            firing_count += 1
        elif alert.status == 'resolved':
            resolved_count += 1
    
    return {
        'app_id': app_id,
        'time_range': time_range,
        'generated_at': datetime.now().isoformat(),
        'alerts': formatted_alerts,
        'summary': {
            'total': len(alerts),
            'firing': firing_count,
            'resolved': resolved_count
        }
    }


async def get_active_alerts(db: Session, app_id: int):
    ''' Get currently active alerts for an app '''
    alerts = AlertHistoryCrud.get_active_alerts(db, app_id)
    
    formatted_alerts = []
    for alert in alerts:
        formatted_alerts.append({
            'id': alert.id,
            'alert_name': alert.alert_name,
            'status': alert.status,
            'severity': alert.severity,
            'summary': alert.summary,
            'description': alert.description,
            'labels': json.loads(alert.labels) if alert.labels else {},
            'triggered_at': alert.created_at.isoformat()
        })
    
    return {
        'app_id': app_id,
        'active_alerts': formatted_alerts,
        'count': len(formatted_alerts)
    }


async def get_combined_report(db: Session, app_id: int, time_range: str = '1h'):
    ''' Get a combined report with stats and alerts '''
    stats_report = await get_container_stats_report(db, app_id, time_range)
    alerts_report = await get_alert_history_report(db, app_id, time_range)
    
    return {
        'app_id': app_id,
        'time_range': time_range,
        'generated_at': datetime.now().isoformat(),
        'stats': stats_report,
        'alerts': alerts_report
    }
