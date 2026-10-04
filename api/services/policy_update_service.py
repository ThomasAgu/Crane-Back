# policy_update_service.py

from fastapi import Depends
from api.clients.opa_client import update_policies_file
from api.config.constants import OPA_RBAC_CONFIG_FILE, OPA_RBAC_CONFIG_NAME
from api.services.rbac_policy_service import build_dynamic_rego, parse_role_permissions_from_rego, write_rego_file
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.db.crud.permission_crud import populate_roles_and_permissions 
from api.db.crud.role_crud import create as create_role
from api.db.crud.permission_crud import create as create_permission
from api.db.crud.role_crud import assign_permission_to_role
from api.db.crud.role_crud import delete_all as delete_all_roles
from api.db.crud.permission_crud import delete_all as delete_all_permissions
from api.db.crud.role_permission_crud import delete_all as delete_all_role_permissions    

def update_opa_policies_from_db(db):
    """
    1. Build dynamic Rego from DB
    2. Generate temp file
    3. Update OPA policies
    """
    rego = build_dynamic_rego(db)
    path = write_rego_file(rego)
    print("Archivo generado:", path)

        
    # Usa tu método actual
    return update_policies_file(OPA_RBAC_CONFIG_NAME, path, force=True)

def update_or_create_roles_and_permissions_in_db():
    """
    Sync DB roles, permissions, and role_permissions with the RBAC Rego file.
    """
    with next(get_db()) as db:

        delete_all_roles_and_permissions(db)

        rego_path = OPA_RBAC_CONFIG_FILE 
        role_permissions = parse_role_permissions_from_rego(rego_path)
        populate_roles_and_permissions(db, role_permissions)


def delete_all_roles_and_permissions(db: Session = Depends(get_db)):
        delete_all_roles(db)
        delete_all_permissions(db)
        delete_all_role_permissions(db)