import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from starlette import status
from starlette.exceptions import HTTPException
from api.db import models, schemas
from api.db.models import RepositoryItem

def get_by_name(db: Session, name: str, user_id: int = None):
    ''' Get app by name '''
    return db.query(models.App).filter(and_(models.App.name == name, models.App.deleted_at == None)).filter(or_(models.App.user_id == user_id, user_id is None)).first()


def get_by_id(db: Session, app_id: int, user_id: int = None):
    ''' Get app by id '''
    return db.query(models.App).filter(and_(models.App.id == app_id, models.App.deleted_at == None)).filter(or_(models.App.user_id == user_id, user_id is None)).first()

def get_by_name_and_user_id(db: Session, name: str, user_id: int):
    ''' Get app by name and user_id '''
    return db.query(models.App).filter(and_(models.App.name == name, models.App.user_id == user_id, models.App.deleted_at == None)).first()

def get_all(db: Session, user_id: int = None, skip: int = 0, limit: int = 100):
    ''' Get all apps '''
    return db.query(models.App).filter(models.App.deleted_at == None).filter(or_(models.App.user_id == user_id, user_id is None)).offset(skip).limit(limit).all()

def get_all_by_service(db: Session, skip: int = 0, limit: int = 100):
    # Should be good if we only retrieve apps that have services defined, which should be the majority of them. We can add more filters if needed.
    ''' Get all apps by service '''
    return db.query(models.App).filter(models.App.deleted_at == None).offset(skip).limit(limit).all()

def create(db: Session, user_app: schemas.AppCreate):
    ''' Create app '''
    # 1. Convertimos el schema a diccionario
    # (Nota: si usas Pydantic v2, es mejor usar .model_dump() en vez de .dict())
    app_dict = user_app.dict() if hasattr(user_app, 'dict') else user_app.model_dump()
    
    # 2. Serializamos lo que va como string/JSON a la base de datos
    # Usamos .get() por seguridad o fallback a listas vacías
    services_list = app_dict.get("services") or []
    hosts_list = app_dict.get("hosts") or []
    
    # Si los servicios vienen como objetos de Pydantic complejos dentro de la lista,
    # nos aseguramos de convertirlos a diccionarios puros antes del json.dumps
    clean_services = [
        s.dict() if hasattr(s, 'dict') else (s.model_dump() if hasattr(s, 'model_dump') else s)
        for s in services_list
    ]
    
    app_dict["services"] = json.dumps(clean_services)
    app_dict["hosts"] = json.dumps(hosts_list)

    # 3. FILTRAR CAMPOS: Extraemos campos que pertenecen al schema de API
    # pero no a la tabla apps, para que no se envíen al constructor de SQLAlchemy.
    app_dict.pop("environment", None)
    app_dict.pop("repository_state", None)
    app_dict.pop("repository_updated_at", None)
    # Extraemos 'alerts' enviadas desde el frontend para evitar pasar claves
    # desconocidas al constructor de SQLAlchemy (models.App no tiene ese campo)
    app_dict.pop("alerts", None)
    # Si 'startup_scripts' o cualquier otra propiedad estuviera a nivel de App, la sacas acá también:
    # app_dict.pop("startup_scripts", None)

    # 4. Ahora sí, instanciamos el modelo de la DB sin peligro de invalid keywords
    db_app = models.App(**app_dict)

    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

def update(db: Session, app: schemas.App):
    ''' Update app '''
    services = app.services or []
    clean_services = [
        service.model_dump() if hasattr(service, 'model_dump')
        else service.dict() if hasattr(service, 'dict')
        else service
        for service in services
    ]
    app.services = json.dumps(clean_services)
    app.hosts = json.dumps(app.hosts or [])

    db.commit()
    db.refresh(app)
    return app


def delete_logical(db: Session, app_id: str, user_id: int = None):
    ''' Logical delete app '''
    db_app = get_by_id(db, app_id, user_id)
    db_app.deleted_at = datetime.now()
    db.commit()
    return db_app


def delete_physical(db: Session, app_id: int, user_id: int = None):
    """Delete app physically from database. Repository check should be done before calling this."""
    db_app = get_by_id(db, app_id, user_id)
    
    if not db_app:
        return None

    db.delete(db_app)
    db.commit()
    
    return db_app