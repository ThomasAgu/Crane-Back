from sqlalchemy.orm import Session
from api.db import models, schemas


def get_all(db: Session, skip: int = 0, limit: int = 100):
    ''' Get all roles '''
    return db.query(models.Role).offset(skip).limit(limit).all()


def get_by_id(db: Session, role_id: int):
    ''' Get role by ID '''
    return db.query(models.Role).filter(models.Role.id == role_id).first()

def get_permissions_for_role(db: Session, role_id: int):
    ''' Get all permissions for a role '''
    role = get_by_id(db, role_id)

    if not role:
        return None

    return (
        db.query(models.Permission)
        .join(models.RolePermission, models.RolePermission.permission_id == models.Permission.id)
        .filter(models.RolePermission.role_id == role_id)
        .all()
    )


def get_by_name(db: Session, name: str):
    ''' Get role by name '''
    return db.query(models.Role).filter(models.Role.name == name).first()


def create(db: Session, role: schemas.RoleCreate):
    ''' Create a new role '''
    db_role = models.Role(**role.dict())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def update(db: Session, role_id: int, role: schemas.RoleUpdate):
    ''' Update a role '''
    db_role = db.query(models.Role).filter(
        models.Role.id == role_id).first()
    if not db_role:
        return None

    for key, value in role.dict().items():
        setattr(db_role, key, value)

    db.commit()
    db.refresh(db_role)
    return db_role


def delete(db: Session, role_id: int):
    ''' Delete a role '''
    db_role = db.query(models.Role).filter(
        models.Role.id == role_id).first()
    if not db_role:
        return None

    db.delete(db_role)
    db.commit()
    return db_role


def create_for_user(db: Session, user_id: int, role_id: int):
    ''' Create a new role for a user '''
    db_user_role = models.UserRole(user_id=user_id, role_id=role_id)
    db.add(db_user_role)
    db.commit()
    db.refresh(db_user_role)
    return db_user_role


def remove_user(db: Session, user_id: int, role_id: int):
    ''' Remove a role from a user '''
    db_user_role = db.query(models.UserRole).filter(
        models.UserRole.role_id == role_id,
        models.UserRole.user_id == user_id
    ).first()
    if not db_user_role:
        return None

    db.delete(db_user_role)
    db.commit()
    return db_user_role


def get_roles_by_user(db: Session, db_user: models.User):
    ''' Get roles by user '''
    return db.query(models.Role).join(models.UserRole).filter(models.UserRole.user_id == db_user.id).all()

def assign_permission_to_role(db: Session, role_id: int, permission_id: int):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    permission = db.query(models.Permission).filter(models. Permission.id == permission_id).first()

    if not role or not permission:
        return None

    # verificar si ya existe
    existing = (
        db.query(models.RolePermission)
        .filter(
            models.RolePermission.role_id == role_id,
            models.RolePermission.permission_id == permission_id
        )
        .first()
    )
    if existing:
        return False

    rp = models.RolePermission(role_id=role_id, permission_id=permission_id)
    db.add(rp)
    db.commit()
    db.refresh(rp)

    return rp

def delete_permission_from_role(db: Session, role_id: int, permission_id: int):
    permission = db.query(models.Permission).filter(models.Permission.id == permission_id).first()

    if not permission:
        return None

    rp = (
        db.query(models.RolePermission)
        .filter(
            models.RolePermission.role_id == role_id,
            models.RolePermission.permission_id == permission_id
        )
        .first()
    )
    
    if not rp:
        return False

    db.delete(rp)
    db.commit()

    return rp