'''
This module contains the service functions for user operations
'''
import api.db.crud.user_crud as UserCrud
import api.services.role_service as RoleService
import api.services.group_service as GroupService
import api.services.repository_item_service as RepositoryService

async def get_users(db):
    ''' Get all users '''
    users = UserCrud.get_all(db)
    return users

async def get_by_id(db, user_id: int):
    ''' Get user by ID '''
    user = UserCrud.get_by_id(db, user_id)

    # traer los grupos
    groups = await GroupService.get_groups_by_user_id(db, user_id)

    # traer los repositorios
    repositories = await RepositoryService.get_repository_items(db, user_id)

    # armar un objeto con las 3 cosas
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "groups": groups,
        "repositories": repositories
    }

async def get_users_with_roles(db):
    users = await get_users(db)
    result = []
    for user in users:
        roles = await RoleService.get_roles_by_user_id(db, user.id)
        result.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "roles": roles
        })
    return result

async def disable_user(db, user_id: int):
    ''' Disable a user by ID '''
    user = UserCrud.disable_user(db, user_id)
    return user

async def enable_user(db, user_id: int):
    ''' Enable a user by ID '''
    user = UserCrud.enable_user(db, user_id)
    return user