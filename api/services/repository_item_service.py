''' Service layer for managing repository items. '''
from api import db
import api.db.crud.repository_item as repositoryItemCrud
import api.db.crud.vote_crud as voteCrud
import api.db.crud.favourite_crud as favouriteCrud
import api.db.schemas as schemas
import api.db.crud.notification_crud as notificationCrud
import api.db.models as models
from fastapi import HTTPException

from api.services.crane_service import copy as copy_app_service


async def get_repository_items(db, user_id: int):
    ''' Get all repository items '''
    repository_items = repositoryItemCrud.get_all(db, user_id)
    return repository_items

async def get_repository_item_by_id(db, repository_item_id: int, user_id: int):
    ''' Get repository item by ID '''
    repository_item = repositoryItemCrud.get_by_id_with_stats(db, repository_item_id, user_id)
    return repository_item

async def vote_up_repository_item(db, user_id: int, repository_item_id: int):
    ''' Vote up a repository item '''
    voteCrud.add_vote(db, user_id=user_id, repository_item_id=repository_item_id, vote_type='up')
    
    # Conseguimos el item
    repository_item = repositoryItemCrud.get_by_id(db, repository_item_id)
    
    # Creamos el objeto de validación de Pydantic
    notification_data = schemas.NotificationCreate(
        user_id=repository_item.user_id,
        name=f"Voto positivo en tu item '{repository_item.name}'",
        description=f"Tu repositorio '{repository_item.name}' recibio un voto positivo!"
    )
    # Se lo pasamos al CRUD
    notificationCrud.create(db, notification=notification_data)
    
    return repositoryItemCrud.get_by_id_with_stats(db, repository_item_id, user_id)


async def vote_down_repository_item(db, user_id: int, repository_item_id: int):
    ''' Vote down a repository item '''
    voteCrud.add_vote(db, user_id=user_id, repository_item_id=repository_item_id, vote_type='down')
    '''Add a notification for the owner of the repository item when it receives a new downvote'''
    repository_item = repositoryItemCrud.get_by_id(db, repository_item_id)
    notification_data = schemas.NotificationCreate(
        user_id=repository_item.user_id,
        name=f"Voto negativo en tu item '{repository_item.name}'",
        description=f"Tu repositorio '{repository_item.name}' recibio un voto negativo!"
    )
    notificationCrud.create(db, notification=notification_data)
    return repositoryItemCrud.get_by_id_with_stats(db, repository_item_id, user_id)
    
async def favourite_repository_item(db, user_id: int, repository_item_id: int):
    ''' Favourite a repository item '''
    favouriteCrud.add_favourite(db, user_id, repository_item_id)
    '''Add a notification for the owner of the repository item when it receives a new favourite'''
    repository_item = repositoryItemCrud.get_by_id(db, repository_item_id)
    notification_data = schemas.NotificationCreate(
        user_id=repository_item.user_id,
        name=f"Tu item '{repository_item.name}' recibio un nuevo favorito!",
        description=f"Tu repositorio '{repository_item.name}' recibio un nuevo favorito!"
    )
    notificationCrud.create(db, notification=notification_data)
    return repositoryItemCrud.get_by_id_with_stats(db, repository_item_id, user_id)

async def download_repository_item(db, user_id: int, repository_item_id: int):
    ''' Create a copy of an app from logged user and increment download count for a repository item '''
    #Get repository item to access app_id
    repository_item = repositoryItemCrud.get_by_id(db, repository_item_id) 
    # Copy app associated to repository item
    await copy_app_service(db, repository_item.app_id, user_id)
    # Increment download count
    repositoryItemCrud.download(db, repository_item_id)
    # Return new stats
    return repositoryItemCrud.get_by_id_with_stats(db, repository_item_id, user_id)

async def create_repository_item(db, name: str, description: str, services: str, app_id: int, user_id: int):
    ''' Create a new repository item '''
    repository_item = repositoryItemCrud.create(db, name, description, services, app_id, user_id)
    '''Add a notification for the owner of the repository item when the repository item is pending to approve'''
    notification_data = schemas.NotificationCreate(
        user_id=repository_item.user_id,
        name=f"Your repository item '{repository_item.name}' is pending approval!",
        description=f"Your repository item '{repository_item.name}' is pending approval!"
    )
    notificationCrud.create(db, notification=notification_data)
    return repository_item

async def update_repository_item(db, name: str, description: str, services: str, app_id: int, user_id: int):
    ''' Update an existing repository item based on its app_id '''
    
    # 1. Buscar el repository item existente usando el app_id
    repository_item = repositoryItemCrud.get_by_app_id(db, app_id)
    
    if not repository_item:
        # Puedes manejar esto con una excepción de FastAPI o retornar None
        raise HTTPException(status_code=404, detail="Repository item not found for this app")
        
    # 2. Preparar los datos actualizados. 
    updated_data = {
        "name": name,
        "description": description,
        "services": services,
        "state": "pending",  
        "user_id": user_id
    }
    
    # 3. Llamar al CRUD para actualizar el registro
    repository_item = repositoryItemCrud.update(db, db_obj=repository_item, obj_in=updated_data)
    
    # 4. Enviar notificación de que volvió a quedar pendiente de aprobación
    notification_data = schemas.NotificationCreate(
        user_id=repository_item.user_id,
        name=f"Your repository item '{repository_item.name}' has been updated and is pending approval!",
        description=f"The repository item '{repository_item.name}' was modified and needs to be re-approved."
    )
    notificationCrud.create(db, notification=notification_data)
    
    return repository_item

async def approve_repository_item(db, repository_item_id: int):
    ''' Approve a repository item '''
    repository_item = repositoryItemCrud.approve(db, repository_item_id)
    '''Add a notification for the owner of the repository item when the repository item is approved'''
    notification_data = schemas.NotificationCreate(
        user_id=repository_item.user_id,
        name=f"Your repository item '{repository_item.name}' has been approved!",
        description=f"Your repository item '{repository_item.name}' has been approved!"
    )
    notificationCrud.create(db, notification=notification_data)
    return repository_item

async def reject_repository_item(db, repository_item_id: int):
    ''' Reject a repository item '''
    repository_item = repositoryItemCrud.reject(db, repository_item_id)
    '''Add a notification for the owner of the repository item when the repository item is rejected'''
    notification_data = schemas.NotificationCreate(
        user_id=repository_item.user_id,
        name=f"Your repository item '{repository_item.name}' has been rejected!",
        description=f"Your repository item '{repository_item.name}' has been rejected!"
    )
    notificationCrud.create(db, notification=notification_data)
    return repository_item

async def delete_repository_item(db, repository_item_id: int):
    ''' Delete a repository item '''
    repository_item = repositoryItemCrud.delete(db, repository_item_id)
    return repository_item