'''This file contains the schema for the container model'''
from typing import Optional
from pydantic import BaseModel


class Container (BaseModel):
    id: Optional[str]
    name: Optional[str]
    image: Optional[str]
    network: Optional[str]
    count: Optional[int]
    command: Optional[str]
    ports: Optional[str]
    volumes: Optional[str]
    environment: Optional[str]
    labels: Optional[str]
