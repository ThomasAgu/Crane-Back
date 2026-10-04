from sqlalchemy.orm import Session
from api.db import models, schemas

def get_by_id(db: Session, task_id: int):
    ''' Get a task by ID '''
    return db.query(models.GroupTask).filter(models.GroupTask.id == task_id).first()

def create(db: Session, task: schemas.TaskGroupCreate):
    ''' Create a new task and assign it to a group '''
    db_task = models.GroupTask(**task.dict())
    # Revisar que la task exista
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete(db: Session, task_group_id: int):
    ''' remove task from group by task ID '''
    task = db.query(models.GroupTask).filter(models.GroupTask.id == task_group_id).first()
    if task:
        db.delete(task)
        db.commit()
    return task

def get_tasks_by_group_id(db: Session, group_id: int):
    ''' Get tasks assigned to a group by group ID '''
    return db.query(models.GroupTask).filter(models.GroupTask.group_id == group_id).all()