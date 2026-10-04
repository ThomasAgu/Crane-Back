from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.schemas import TaskCreate, TaskGroupCreate
from api.routes.auth_routes import verify_jwt
from api.services import task_service as TaskService
from fastapi import Body

taskRouter = APIRouter()

@taskRouter.get(
    "/",
    tags=["Tasks"],
    description="Get tasks created by logged User",
    response_model_exclude_none=True,
    dependencies=[Depends(verify_jwt)]  
)
async def get_tasks(db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
  
  return await TaskService.get_tasks_created_by_user(db, db_user.id) 

@taskRouter.get(
  "/{task_id}",
  tags=["Tasks"],
  description="Get a task by ID",
  response_model_exclude_none=True,
  dependencies=[Depends(verify_jwt)]
)
async def get_task(task_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
  return await TaskService.get_task_by_id(db, task_id, db_user.id)

@taskRouter.post(
  "/",
  tags=["Tasks"],
  description="Create a new task",
  response_model_exclude_none=True,
  dependencies=[Depends(verify_jwt)]
)
async def create_task(
  task_data: TaskCreate, 
  db_user=Depends(verify_jwt), 
  db: Session = Depends(get_db),
  dependencies=[Depends(verify_jwt)]
  ):
  return await TaskService.create_task(db, task_data, db_user.id)

@taskRouter.delete(
  "/{task_id}",
  tags=["Tasks"],
  description="Delete a task by ID",
  dependencies=[Depends(verify_jwt)]
)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
  return await TaskService.delete_task(db, task_id)

@taskRouter.post(
  "/assign",
  tags=["Tasks"],
  description="Assign a task to a group",
  dependencies=[Depends(verify_jwt)],
  response_model_exclude_none=True,
)
async def assign_task_to_group(
  task_group_data: TaskGroupCreate,
  db_user=Depends(verify_jwt), 
  db: Session = Depends(get_db)
):
  return await TaskService.assign_task_to_group(db, task_group_data)

@taskRouter.post(
  "/remove/{task_group_id}",
  tags=["Tasks"],
  description="Remove a task from a group",
  response_model_exclude_none=True,
  dependencies=[Depends(verify_jwt)]
)
async def remove_task_from_group(
  task_group_id: int,
  db_user=Depends(verify_jwt), 
  db: Session = Depends(get_db)
  ):
  return await TaskService.remove_task_from_group(db, task_group_id)


