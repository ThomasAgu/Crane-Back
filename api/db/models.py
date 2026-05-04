''' This module defines the database models '''
from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship


from .database import Base


class User(Base):
    ''' This class defines the user model '''
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    apps = relationship("App", back_populates="user")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)


class Role(Base):
    ''' This class defines the role model '''
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    built_in = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)


class UserRole(Base):
    ''' This class defines the user role model '''
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)


class App(Base):
    ''' This class defines the app model '''
    __tablename__ = "apps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    services = Column(String, index=True)
    min_scale = Column(Integer, index=True, default=1)
    current_scale = Column(Integer, index=True, default=1)
    max_scale = Column(Integer, index=True, default=2)
    hosts = Column(String, index=True)
    force_stop = Column(Boolean, index=True, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="apps")
    custom_alerts = relationship("CustomAlert", back_populates="app")
    app_policies = relationship("AppPolicy", back_populates="app")


class Permission(Base):
    ''' This class defines the permission model '''
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    object = Column(String, index=True)
    action = Column(String, index=True)
    description = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)

class RolePermission(Base):
    ''' This class defines the role permission model '''
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)

class RepositoryItem(Base):
    ''' This class defines the repository item model '''
    __tablename__ = "repository_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    services = Column(String, index=True)
    downloads = Column(Integer, default=0)
    state = Column(String, default="pending")
    app_id = Column(Integer, ForeignKey("apps.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)

class Vote(Base):
    ''' This class defines the vote model '''
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    repository_item_id = Column(Integer, ForeignKey("repository_items.id"))
    vote_type = Column(String, index=True) 
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)

class Favourite(Base):
    ''' This class defines the favourite model '''
    __tablename__ = "favourites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    repository_item_id = Column(Integer, ForeignKey("repository_items.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)

class CustomAlert(Base):
    __tablename__ = 'custom_alerts'

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey('apps.id'), nullable=False)
    alert = Column(String, nullable=False)
    expr = Column(Text, nullable=False)
    for_time = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    deleted_at = Column(String, index=True)

    app = relationship("App", back_populates="custom_alerts")
    app_policies = relationship("AppPolicy", back_populates="alert")

class AppPolicy(Base):
    __tablename__ = 'app_policies'

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey('apps.id'), nullable=False)
    alert_id = Column(Integer, ForeignKey('custom_alerts.id'), nullable=False)
    firing_action = Column(String, nullable=False)
    resolved_action = Column(String, nullable=False)

    app = relationship("App", back_populates="app_policies")
    alert = relationship("CustomAlert", back_populates="app_policies")

class Action(Base): 
    __tablename__ = 'firing_actions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

class Scenario(Base):
    __tablename__ = 'scenarios'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    function_name = Column(Text, nullable=False)

class ContainerStats(Base):
    '''This class defines the container stats model for historical tracking'''
    __tablename__ = 'container_stats'

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey('apps.id'), nullable=False, index=True)
    container = Column(String, nullable=False, index=True)  # Container identifier
    container_id = Column(String, nullable=False)  # Full container ID
    container_name = Column(String, nullable=False, index=True)  # Container name
    cpu_percentage = Column(String, nullable=False)  # CPU percentage
    memory_used = Column(String, nullable=False)  # Memory used in bytes
    memory_limit = Column(String, nullable=False)  # Memory limit in bytes
    memory_percentage = Column(String, nullable=False)  # Memory percentage
    net_upload = Column(String, nullable=False)  # Network upload in bytes
    net_download = Column(String, nullable=False)  # Network download in bytes
    block_read = Column(String, nullable=False)  # Block read in bytes
    block_write = Column(String, nullable=False)  # Block write in bytes
    created_at = Column(DateTime, default=datetime.now, index=True)

class AlertHistory(Base):
    '''This class defines the alert history model for tracking triggered alerts'''
    __tablename__ = 'alert_history'

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey('apps.id'), nullable=False, index=True)
    alert_id = Column(Integer, ForeignKey('custom_alerts.id'), nullable=True)
    alert_name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)  # 'firing' or 'resolved'
    severity = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    labels = Column(Text, nullable=True)  # JSON string of labels
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, onupdate=datetime.now)