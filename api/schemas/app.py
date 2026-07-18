''' This file contains the schema for the app model. '''
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class VolumeConfig(BaseModel):
    path: str
    size: Optional[int] = None

class NetworkConfig(BaseModel):
    name: str
    driver: Optional[str] = "default"
    address: Optional[str] = None
    mask: Optional[int] = None
    gateway: Optional[str] = None

class ResourceLimits(BaseModel):
    cpus: Optional[str] = None
    memory: Optional[str] = None

class ResourceConfig(BaseModel):
    limits: Optional[ResourceLimits] = None

class Service(BaseModel):
    name: str
    image: str
    command: Optional[str] = None
    ports: Optional[List[str]] = Field(default_factory=list)
    volumes: Optional[List[VolumeConfig]] = Field(default_factory=list)
    networks: Optional[List[NetworkConfig]] = Field(default_factory=list)
    labels: Optional[List[str]] = Field(default_factory=list)
    environment: Optional[Dict[str, str]] = Field(default_factory=dict)
    restart_policy: Optional[str] = Field(default="unless-stopped", alias="restart_policy")
    resources: Optional[ResourceConfig] = None
    startup_scripts: Optional[List[Any]] = Field(default_factory=list)

class App(BaseModel):
    id: Optional[int] = None
    name: str
    services: List[Service] = Field(default_factory=list) # Ahora usa el schema Service
    hosts: Optional[List[str]] = Field(default_factory=list)
    min_scale: Optional[int] = 0
    current_scale: Optional[int] = 1
    max_scale: Optional[int] = 1
    force_stop: Optional[bool] = False
    environment: Optional[Dict[str, str]] = Field(default_factory=dict) # Env globales de la App
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    user_id: Optional[int] = None
    is_uploaded: bool = False

class Service(BaseModel):
    ''' This class defines the service schema contained in the app schema '''
    name: str
    image: str
    command: Optional[str] = None
    ports: Optional[list] = None
    volumes: Optional[list] = None
    networks: Optional[list] = None
    labels: Optional[list] = None

class AppDocker(App):
    ''' This class defines the app schema with docker dynamic fields '''
    docker: Optional[list] = None
    ip: Optional[str] = None
    ports: Optional[dict] = None
    status: Optional[str] = None


class ProxyRoute(BaseModel):
    ''' This class defines the proxy route schema '''
    ip: Optional[str] = None
    ports: Optional[dict] = None
    status: Optional[str] = None
