from sqlalchemy.orm import Session, joinedload
from api.db import models, schemas
from api.db.crud.user_group_crud import create as add_user_to_user_group, delete as remove_user_from_user_group
from api.db.crud.notification_crud import create as create_notification

def get_groups_by_user_id(db: Session, user_id: int):
    return (
        db.query(models.Group)
        # 1. Filtramos para que solo traiga los grupos donde está el usuario
        .join(models.Group.user_groups)
        .filter(models.UserGroup.user_id == user_id)
        # 2. Precargamos (Eager Loading) las relaciones anidadas tal como en tu get_by_id
        .options(
            joinedload(models.Group.user_groups).joinedload(models.UserGroup.user),
            joinedload(models.Group.tasks)
        )
        .all()
    )

def get_created_by_user_id(db: Session, user_id: int):
    ''' Get groups created by a user ID '''
    return db.query(models.Group).filter(models.Group.created_by == user_id).all()

def get_by_id(db: Session, group_id: int):
    ''' Get a group by ID with all members (including user info) and tasks (with intermediate data) '''
    return db.query(models.Group)\
        .options(
            # Carga miembros del grupo y la info de sus usuarios
            joinedload(models.Group.user_groups).joinedload(models.UserGroup.user),
            
            # Carga la tabla intermedia (GroupTask) Y ADEMÁS la entidad Task asociada
            joinedload(models.Group.tasks).joinedload(models.GroupTask.task)
        )\
        .filter(models.Group.id == group_id)\
        .first()

def create(db: Session, group: schemas.GroupCreate, created_by: int):
    ''' Create a new group '''
    group_data = group.dict(exclude={'member_ids'})
    db_group = models.Group(**group_data)
    
    db_group.created_by = created_by
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    # ID 4 = Professor
    add_user_to_group(db, db_group.created_by, db_group.id, 4)

    if group.member_ids:
        for member_id in group.member_ids:
            #ID 5 = Student
            add_user_to_group(db, member_id, db_group.id, 5)
            
            notification_data = schemas.NotificationCreate(
                user_id=member_id,
                name="Nuevo Grupo",
                description=f"Fuiste agregado al grupo: {db_group.name}"
            )
            create_notification(db, notification_data)

    return db_group

def delete(db: Session, group_id: int):
    ''' Delete a group by ID '''
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if group:
        db.delete(group)
        db.commit()
        return True
    return False

def add_user_to_group(db: Session, user_id: int, group_id: int, role_id: int):
    ''' Add a user to a group with a specific role '''
    group = get_by_id(db, group_id)
    if not group:
        return None

    # Verificar si el usuario ya es miembro del grupo
    existing_member = db.query(models.UserGroup).filter(
        models.UserGroup.group_id == group_id,
        models.UserGroup.user_id == user_id
    ).first()

    if existing_member:
        return existing_member  # El usuario ya es miembro del grupo

    # Crear una nueva entrada en UserGroup
    user_group = schemas.UserGroupCreate(
        user_id=user_id,
        group_id=group_id,
        # puede tener varios roles, por ejemplo: "student", "professor", "assistant"
        role_id=role_id
    )

    new_member = add_user_to_user_group(db, user_group)
    return new_member

def remove_user_from_group(db: Session, group_id: int, user_id: int):
    ''' Remove a user from a group '''
    user_group = db.query(models.UserGroup).filter(
        models.UserGroup.group_id == group_id,
        models.UserGroup.user_id == user_id
    ).first()
    
    if user_group:
        return remove_user_from_user_group(db, user_group.id)
    return None
