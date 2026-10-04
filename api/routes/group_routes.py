from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from api.db.schemas import GroupCreate
from api.db.schemas import UserGroupCreate, UserGroupRemove

from api.db.database import get_db
from api.routes.auth_routes import verify_jwt
from api.services import group_service as GroupService

groupRouter = APIRouter()

@groupRouter.get(
  "/",
  tags=["Groups"],
  description="Get groups associated with a user ID",
  response_model_exclude_none=True,
  dependencies=[Depends(verify_jwt)]
)
async def get_groups_by_user_id(db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
  return await GroupService.get_groups_by_user_id(db, db_user.id) 

@groupRouter.get(
  "/{group_id}",
  tags=["Groups"],
  description="Get a group by ID",
  response_model_exclude_none=True,
  dependencies=[Depends(verify_jwt)]
)
async def get_group_by_id(group_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
  return await GroupService.get_group_by_id(db, group_id)

@groupRouter.post(
  "/",
  tags=["Groups"],
  description="Create a new group",
  response_model_exclude_none=True,
  dependencies=[Depends(verify_jwt)]
)
async def create_group(
  group_data: GroupCreate, 
  db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
  return await GroupService.create_group(db, group_data, db_user.id)

@groupRouter.delete(
  "/{group_id}",
  tags=["Groups"],
  description="Delete a group by ID",
  response_model_exclude_none=True,
  dependencies=[Depends(verify_jwt)]
)
async def delete_group(group_id: int, db: Session = Depends(get_db)):
  return await GroupService.delete_group(db, group_id)

@groupRouter.post(
  "/add_user",
  tags=["Groups"],
  description="Add a user to a group with a specific role",
  response_model_exclude_none=True,
  dependencies=[Depends(verify_jwt)]
)
async def add_user_to_group(
  data: UserGroupCreate,
  db_user=Depends(verify_jwt), 
  db: Session = Depends(get_db),
):
  return await GroupService.add_user_to_group(db, data.user_id, data.group_id, data.role_id)

@groupRouter.post(
  "/remove_user",
  tags=["Groups"],
  description="Remove a user from a group",
  response_model_exclude_none=True,
  dependencies=[Depends(verify_jwt)]
)
async def remove_user_from_group(
  data: UserGroupRemove,
  db_user=Depends(verify_jwt), 
  db: Session = Depends(get_db)):
  return await GroupService.remove_user_from_group(db, data.group_id, data.user_id)
