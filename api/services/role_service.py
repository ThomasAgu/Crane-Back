'''
This module contains the service functions for role operations
'''
import api.db.crud.role_crud as RoleCrud
import api.db.crud.user_crud as UserCrud
async def get_roles_by_user_id(db, user_id: int):
    ''' Get all roles by user ID '''
    user = UserCrud.get_by_id(db, user_id)
    return RoleCrud.get_roles_by_user(db, user)