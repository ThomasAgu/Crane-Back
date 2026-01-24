''' This module contains the CRUD operations for the User model. '''
from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Session
from api.config.constants import SECRET_KEY
from api.db import models, schemas


def get_all(db: Session, skip: int = 0, limit: int = 100):
    ''' Get all users '''
    return db.query(models.User).offset(skip).limit(limit).all()


def get_by_id(db: Session, user_id: int):
    ''' Get user by ID '''
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_by_email(db: Session, email: str):
    ''' Get user by email '''
    return db.query(models.User).filter(models.User.email == email.strip()).first()


def register(db: Session, user: schemas.UserCreate):
    ''' Register a new user '''
    hashed_password = pbkdf2_sha256.hash(user.password, salt=SECRET_KEY)
    db_user = models.User(
        email=user.email,
        password=hashed_password,
        full_name=user.full_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def disable_user(db: Session, user_id: int):
    ''' Disable a user by ID '''
    user = get_by_id(db, user_id)
    if user:
        user.is_active = False
        db.commit()
        db.refresh(user)
    return user

def enable_user(db: Session, user_id: int):
    ''' Enable a user by ID '''
    user = get_by_id(db, user_id)
    if user:
        user.is_active = True
        db.commit()
        db.refresh(user)
    return user

def login(db: Session, user: schemas.UserLogin):
    ''' Login to get an authentication token '''
    db_user = get_by_email(db, user.email)
    if db_user:
        if pbkdf2_sha256.verify(user.password, db_user.password):
            return db_user
    return None
