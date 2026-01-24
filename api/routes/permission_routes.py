''' This module contains the routes for the Permission model.'''
from typing import List
from api.services.policy_update_service import update_opa_policies_from_db
from fastapi import Depends
from api.routes.auth_routes import verify_jwt
from api.db.schemas import Permission
from api.db.crud.permission_crud import get_all
from fastapi import APIRouter
from sqlalchemy.orm import Session
from api.db.database import get_db

permissionRouter = APIRouter()

@permissionRouter.get("/", tags=["Permissions"], description="Get all permissions", response_model=List[Permission] , dependencies=[Depends(verify_jwt)])
def get_all_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all(db=db, skip=skip, limit=limit)

@permissionRouter.post(
    "/", 
    tags=["Permissions"], 
    description="Save all permissions and roles (rebuild OPA policies)", 
    dependencies=[Depends(verify_jwt)]
)
def save_permissions_and_roles(db: Session = Depends(get_db)):
    from api.services.policy_update_service import update_opa_policies_from_db

    updated = update_opa_policies_from_db(db)

    return {
        "status": "success",
        "message": "OPA policies updated from database",
        "updated": updated
    }
