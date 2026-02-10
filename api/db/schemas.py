from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class App(BaseModel):
    id: str
    name: str
    services: dict
    command: str
    volumes: dict
    labels: dict
    min_scale: int
    current_scale: int
    max_scale: int
    force_stop: bool
    image: str
    network: str
    hosts: dict
    environment: str
    created_at: str
    updated_at: str
    deleted_at: str
    user_id: int

    class Config:
        from_attributes = True


class AppCreate(App):
    name: str
    services: list
    min_scale: Optional[int] = None
    current_scale: Optional[int] = None
    max_scale: Optional[int] = None
    force_stop: Optional[bool] = None
    hosts: Optional[list] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[str] = None


class UserBase(BaseModel):
    id: Optional[int]
    services: list


class UserCreate(BaseModel):
    full_name: Optional[str]
    email: str
    password: str


class UserUpdate(UserBase):
    password: str
    is_active: bool


class User(UserBase):
    id: int
    is_active: bool
    services: list[App] = []

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str
    password: str


class Role(BaseModel):
    id: Optional[int]
    name: str
    built_in: int
    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    name: str
    built_in: bool = False

class RoleUpdate(BaseModel):
    name: str
    built_in: bool

class UserRole(BaseModel):
    id: Optional[int]
    user_id: int
    role_id: int

    class Config:
        from_attributes = True

class Permission(BaseModel):
    id: Optional[int] = None
    object: str
    action: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RolePermission(BaseModel):
    id: int
    role_id: int
    permission_id: int

    class Config:
        from_attributes = True
