''' This module defines the database models '''
from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
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
