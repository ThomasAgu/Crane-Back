''' Service layer for Task operations '''
from api import db
import api.db.crud.task_crud as taskCrud
import api.db.crud.task_group_crud as taskGroupCrud

async def get_tasks_created_by_user(db, user_id: int):
    ''' Get tasks created by user id'''
    return taskCrud.get_tasks_by_user_id(db, user_id)

async def get_task_by_id(task_id: int):
    ''' Get a task by ID '''
    return taskCrud.get_by_id(db.Session(), task_id)

async def create_task(db, task, user_id: int):
    ''' Create a new task '''
    return taskCrud.create(db, task, user_id)

async def delete_task(db, task_id: int):
    ''' Delete a task by ID '''
    return taskCrud.delete(db, task_id)

async def assign_task_to_group(db, task_group_data):
    ''' Assign a task to a group '''
    return taskGroupCrud.create(db, task_group_data)

async def remove_task_from_group(db, task_group_id: int):
    ''' Remove a task from a group '''
    return taskGroupCrud.delete(db, task_group_id)