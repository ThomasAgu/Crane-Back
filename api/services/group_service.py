''' Service layer for Group operations '''
from api import db
import api.db.crud.group_crud as groupCrud
import api.db.crud.user_group_crud as userGroupCrud

async def get_groups_by_user_id(db, user_id: int):
    ''' Get groups associated with a user ID '''
    return groupCrud.get_groups_by_user_id(db, user_id)

async def get_group_by_id(db, group_id: int):
    ''' Get a group by ID '''
    return groupCrud.get_by_id(db, group_id)

async def create_group(db, group, created_by: int):
    ''' Create a new group '''
    return groupCrud.create(db, group, created_by)

async def delete_group(db, group_id: int):
    ''' Delete a group by ID '''
    return groupCrud.delete(db, group_id)

async def remove_user_from_group(db, group_id: int, user_id: int):
    ''' Remove a user from a group '''
    return groupCrud.remove_user_from_group(db, group_id, user_id)

async def add_user_to_group(db, user_id: int, group_id: int, role_id: int):
    ''' Add a user to a group with a specific role '''
    return groupCrud.add_user_to_group(db, user_id, group_id, role_id)
