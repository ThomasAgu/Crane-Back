from sqlalchemy.orm import Session
from api.db import models

def get_all(db: Session, skip: int = 0, limit: int = 100):
    ''' Get all permissions '''
    return db.query(models.Permission).offset(skip).limit(limit).all()
