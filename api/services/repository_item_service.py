''' Service layer for managing repository items. '''
from api import db
from api.db.crud import app_crud
import api.db.crud.repository_item as repositoryItemCrud
import api.db.crud.vote_crud as voteCrud
import api.db.crud.favourite_crud as favouriteCrud
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
    return repositoryItemCrud.get_by_id_with_stats(db, repository_item_id, user_id)


async def vote_down_repository_item(db, user_id: int, repository_item_id: int):
    ''' Vote down a repository item '''
    voteCrud.add_vote(db, user_id=user_id, repository_item_id=repository_item_id, vote_type='down')
    return repositoryItemCrud.get_by_id_with_stats(db, repository_item_id, user_id)
    
async def favourite_repository_item(db, user_id: int, repository_item_id: int):
    ''' Favourite a repository item '''
    favouriteCrud.add_favourite(db, user_id, repository_item_id)
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
    return repository_item

async def approve_repository_item(db, repository_item_id: int):
    ''' Approve a repository item '''
    repository_item = repositoryItemCrud.approve(db, repository_item_id)
    return repository_item

async def reject_repository_item(db, repository_item_id: int):
    ''' Reject a repository item '''
    repository_item = repositoryItemCrud.reject(db, repository_item_id)
    return repository_item

async def delete_repository_item(db, repository_item_id: int):
    ''' Delete a repository item '''
    repository_item = repositoryItemCrud.delete(db, repository_item_id)
    return repository_item