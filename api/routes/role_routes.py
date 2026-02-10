''' This module contains the routes for the Role model. '''
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.db.crud.role_crud import get_all, get_by_id, create, update, delete, create_for_user, remove_user, get_roles_by_user, get_permissions_for_role, assign_permission_to_role, delete_permission_from_role 
from api.db.schemas import Permission, RoleCreate, RoleUpdate, Role, RolePermission
from api.routes.auth_routes import verify_jwt
from api.db.schemas import UserRole
from api.schemas import user
from api.db.crud import user_crud as UserRepository

roleRouter = APIRouter()


@roleRouter.get("/", tags=["Roles"], description="Get all roles", response_model=List[Role])
def get_all_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all(db=db, skip=skip, limit=limit)


@roleRouter.get("/{role_id}", tags=["Roles"], description="Get role by id", response_model=Role)
def get_role_by_id(role_id: int, db: Session = Depends(get_db)):
    role = get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@roleRouter.get("/user/{user_id}", tags=["Roles"], description="Get all roles for a user ", response_model=List[Role], dependencies=[Depends(verify_jwt)])
def get_user_roles(user_id: int,  db: Session = Depends(get_db)):
    db_user = UserRepository.get_by_id(db, user_id=user_id)
    return get_roles_by_user(db, db_user)

@roleRouter.get(
    "/{role_id}/permissions",
    tags=["Roles"],
    description="Get all permissions for a role",
    response_model=List[Permission],
    dependencies=[Depends(verify_jwt)]
)
def get_permissions_by_role(role_id: int, db: Session = Depends(get_db)):
    permissions = get_permissions_for_role(db, role_id)
    if permissions is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return permissions


@roleRouter.post("/", tags=["Roles"], description="Create a new role", response_model=Role, dependencies=[Depends(verify_jwt)])
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    return create(db=db, role=role)

@roleRouter.post(
    "/{role_id}/permissions/{permission_id}",
    tags=["Roles"],
    description="Assign a permission to a role",
    response_model=RolePermission,
    dependencies=[Depends(verify_jwt)]
)
def add_permission_to_role(role_id: int, permission_id: int, db: Session = Depends(get_db)):
    created = assign_permission_to_role(db, role_id, permission_id)

    if created is None:
        raise HTTPException(status_code=404, detail="Role or Permission not found")

    if created is False:
        raise HTTPException(status_code=400, detail="Permission already assigned to this role")

    return created

@roleRouter.put("/{role_id}", tags=["Roles"], description="Update role", response_model=Role, dependencies=[Depends(verify_jwt)])
def update_role(role_id: int, role: RoleUpdate, db: Session = Depends(get_db)):
    updated_role = update(db, role_id, role)
    if not updated_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return updated_role


@roleRouter.delete("/{role_id}", tags=["Roles"], description="Delete role", response_model=Role, dependencies=[Depends(verify_jwt)])
def delete_role(role_id: int, db: Session = Depends(get_db)):
    deleted_role = delete(db, role_id)
    if not deleted_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return deleted_role


@roleRouter.post("/{role_id}/user/{user_id}", tags=["Roles"], description="Create a role for a user", response_model=UserRole, dependencies=[Depends(verify_jwt)])
def create_role_for_user(user_id: int, role_id: int, db: Session = Depends(get_db)):
    return create_for_user(db, user_id, role_id)

@roleRouter.delete("/{role_id}/user/{user_id}", tags=["Roles"], description="Remove a role from a user", response_model=UserRole, dependencies=[Depends(verify_jwt)])
def remove_role_from_user(user_id: int, role_id: int, db: Session = Depends(get_db)):
    return remove_user(db, user_id, role_id)

@roleRouter.delete(
    "/{role_id}/permissions/{permission_id}",
    tags=["Roles"],
    description="Remove a permission from a role",
    response_model=RolePermission,
    dependencies=[Depends(verify_jwt)]
)
def remove_permission_from_role(role_id: int, permission_id: int, db: Session = Depends(get_db)):
    removed = delete_permission_from_role(db, role_id, permission_id)

    if removed is None:
        raise HTTPException(status_code=404, detail="Role or Permission not found")

    if removed is False:
        raise HTTPException(status_code=400, detail="Permission not assigned to this role")

    return removed

