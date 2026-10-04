from sqlalchemy.orm import Session
from api.db import models, schemas

def get_all(db: Session, skip: int = 0, limit: int = 100):
    ''' Get all permissions '''
    return db.query(models.Permission).offset(skip).limit(limit).all()

def delete_all(db: Session):
    ''' Delete all permissions '''
    db.query(models.Permission).delete()
    db.commit()

def create(db: Session, permission: schemas.Permission):
    ''' Create a new permission '''
    # If `permission` is a Pydantic model, use `dict()`, otherwise assume it's a plain dictionary
    permission_data = permission.dict() if hasattr(permission, "dict") else permission
    db_permission = models.Permission(**permission_data)
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def get_permission_by_object_action(db: Session, object: str, action: str):
    ''' Get permission by object and action '''
    return db.query(models.Permission).filter(
        models.Permission.object == object,
        models.Permission.action == action
    ).first()

def populate_roles_and_permissions(db: Session, role_permissions: dict):
    """
    Populate roles, permissions, and role_permissions tables from the parsed role_permissions dictionary.
    """
    from api.db.crud.role_crud import create as create_role
    from api.db.crud.permission_crud import create as create_permission
    from api.db.crud.role_crud import assign_permission_to_role
    for role_name, permissions in role_permissions.items():
            
        role = create_role(db, schemas.RoleCreate(name=role_name, built_in=True))

        for perm in permissions:
            action = perm["action"]
            obj = perm["object"]
            description = perm.get("description", "")

            existing = get_permission_by_object_action(db, obj, action)

            if existing:
                permission = existing
            else:
                permission = create_permission(
                    db,
                    schemas.Permission(object=obj, action=action, description=description)
                )

            # Assign role-permission
            assign_permission_to_role(db, role.id, permission.id)