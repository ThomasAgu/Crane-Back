''' This file contains the schema for the alert notification. '''
from typing import List, Optional
from pydantic import BaseModel


class GroupLabels(BaseModel):
    alertname: Optional[str] = None


class CommonLabels(BaseModel):
    alertname: Optional[str] = None
    code: Optional[str] = None
    entrypoint: Optional[str] = None
    instance: Optional[str] = None
    job: Optional[str] = None
    method: Optional[str] = None
    monitor: Optional[str] = None
    protocol: Optional[str] = None
    severity: Optional[str] = None


class Annotations(BaseModel):
    description: Optional[str] = None
    summary: Optional[str] = None


class Alert(BaseModel):
    status: Optional[str] = None
    labels: CommonLabels
    annotations: Optional[Annotations] = None
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None
    generatorURL: Optional[str] = None
    fingerprint: Optional[str] = None


class AlertNotification(BaseModel):
    receiver: Optional[str] = None
    status: str
    alerts: List[Alert]
    groupLabels: GroupLabels
    commonLabels: Optional[CommonLabels] = None
    commonAnnotations: Optional[Annotations] = None
    externalURL: Optional[str] = None
    version: Optional[str] = None
    groupKey: Optional[str] = None
    truncatedAlerts: Optional[int] = 0

class CustomAlert(BaseModel):
    alert: str
    expr: str
    for_time: str
    severity: str
    summary: str
    description: str
    firing_action: str
    resolved_action: str