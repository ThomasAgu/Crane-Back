from sqlalchemy.orm import Session
from api.db import models, schemas

def get_all(db: Session, skip: int = 0, limit: int = 100):
    ''' Get all roles '''
    return db.query(models.Action).offset(skip).limit(limit).all()

def create(db: Session, action: schemas.Action):
    ''' Create a new Action '''
    actions_data = action.dict()
    db_actions = models.Action(**actions_data)
    db.add(db_actions)
    db.commit()
    db.refresh(db_actions)
    return db_actions
