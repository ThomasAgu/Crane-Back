from sqlalchemy.orm import Session
from api.db import models, schemas

def get_tasks_by_user_id(db: Session, user_id: int):
    return (
        db.query(models.Task)
        .filter(models.Task.created_by == user_id)
        .all()
    )

def get_by_id(db: Session, task_id: int):
    ''' Get a task by ID '''
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def create(db: Session, task: schemas.TaskCreate, user_id: int):
    ''' Create a new task '''
    task_data = task.dict()
    db_task = models.Task(**task_data)
    db_task.created_by = user_id
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete(db: Session, task_id: int):
    ''' Delete a task by ID '''
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
        return True

    return False