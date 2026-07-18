from sqlalchemy.orm import Session
from api.db import models, schemas

def get_by_id(db: Session, user_group_id: int):
    ''' Get a user group association by ID '''
    return db.query(models.UserGroup).filter(models.UserGroup.id == user_group_id).first()

def create(db: Session, user_group: schemas.UserGroupCreate):
    ''' Assign an user to a group with a specific role '''
    db_user_group = models.UserGroup(**user_group.dict())
    db.add(db_user_group)
    db.commit()
    db.refresh(db_user_group)
    return db_user_group

def delete(db: Session, user_group_id: int):
    ''' Delete a user group association by ID '''
    user_group = db.query(models.UserGroup).filter(models.UserGroup.id == user_group_id).first()
    if user_group:
        db.delete(user_group)
        db.commit()
    return user_group

def get_groups_by_user(db: Session, user_id: int):
    ''' Get groups associated with a user '''
    return db.query(models.UserGroup).filter(models.UserGroup.user_id == user_id).all()

