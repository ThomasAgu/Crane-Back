''' This module contains schemas for reports '''
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ContainerStatPoint(BaseModel):
    ''' Schema for a single container stat data point '''
    timestamp: str
    container: str
    container_id: str
    container_name: str
    cpu_percentage: float
    memory_percentage: float
    memory_used_mb: float
    memory_limit_mb: float
    net_upload_mb: float
    net_download_mb: float
    block_read_mb: float
    block_write_mb: float


class ContainerStatSummary(BaseModel):
    ''' Schema for aggregated container stats '''
    avg_cpu: float
    max_cpu: float
    min_cpu: float
    avg_memory: float
    max_memory: float
    min_memory: float


class StatsReport(BaseModel):
    ''' Schema for container stats report response '''
    app_id: int
    time_range: str
    generated_at: str
    data_points: List[ContainerStatPoint]
    summary: Dict[str, ContainerStatSummary]


class AlertHistoryEvent(BaseModel):
    ''' Schema for a single alert history event '''
    id: int
    alert_name: str
    status: str  # 'firing' or 'resolved'
    severity: Optional[str]
    summary: Optional[str]
    description: Optional[str]
    labels: Dict[str, Any] = {}
    timestamp: str


class AlertsReportSummary(BaseModel):
    ''' Schema for alert report summary '''
    total: int
    firing: int
    resolved: int


class AlertsReport(BaseModel):
    ''' Schema for alert history report response '''
    app_id: int
    time_range: str
    generated_at: str
    alerts: List[AlertHistoryEvent]
    summary: AlertsReportSummary


class ActiveAlert(BaseModel):
    ''' Schema for a currently active alert '''
    id: int
    alert_name: str
    status: str
    severity: Optional[str]
    summary: Optional[str]
    description: Optional[str]
    labels: Dict[str, Any] = {}
    triggered_at: str


class ActiveAlertsReport(BaseModel):
    ''' Schema for currently active alerts report '''
    app_id: int
    active_alerts: List[ActiveAlert]
    count: int


class CombinedReport(BaseModel):
    ''' Schema for combined stats and alerts report '''
    app_id: int
    time_range: str
    generated_at: str
    stats: StatsReport
    alerts: AlertsReport
