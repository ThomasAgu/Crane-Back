'''This module contaiuns the CRUD opertation for the StoreItem model'''

from sqlalchemy import case, func
from sqlalchemy import func
from api.db import models
from api.db.crud.mapper.repository import map_repository_item_result


def get_all(db, user_id: int, skip: int = 0, limit: int = 100):
    ''' Get all repositems '''
    query = build_repository_items_with_stats_query(db, user_id)
    rows = query.offset(skip).limit(limit).all()
    return [map_repository_item_result(row) for row in rows]

def get_by_id_with_stats(db, repository_item_id: int, user_id: int):
    ''' Get repository item by ID '''
    query = build_repository_items_with_stats_query(db, user_id)
    row = query.filter(models.RepositoryItem.id == repository_item_id).first()

    if not row:
        return None

    return map_repository_item_result(row) 

def get_by_state(db, state: str, user_id: int, skip: int = 0, limit: int = 100):
    ''' Get repository items by state '''
    query = build_repository_items_with_stats_query(db, user_id)
    rows = query.filter(models.RepositoryItem.state == state).offset(skip).limit(limit).all()
    return [map_repository_item_result(row) for row in rows]

def get_by_id(db, repository_item_id: int):
    ''' Get repository item by ID without user context '''
    return db.query(models.RepositoryItem).filter(models.RepositoryItem.id == repository_item_id).first()

def build_repository_items_with_stats_query(db, user_id: int):
    votes = func.sum(
        case(
            (models.Vote.vote_type == "up", 1),
            (models.Vote.vote_type == "down", -1),
            else_=0
        )
    ).label("votes")

    favourites = func.count(models.Favourite.id).label("favourites")

    is_favourite = func.sum(
        case(
            (models.Favourite.user_id == user_id, 1),
            else_=0
        )
    ).label("is_favourite")

    is_voted_positive = func.sum(
        case(
            (models.Vote.user_id == user_id,
             case(
                 (models.Vote.vote_type == "up", 1),
                 else_=0
             )),
            else_=0
        )
    ).label("is_voted_positive")

    is_voted_negative = func.sum(
        case(
            (models.Vote.user_id == user_id,
             case(
                 (models.Vote.vote_type == "down", 1),
                 else_=0
             )),
            else_=0
        )
    ).label("is_voted_negative")

    query = (
        db.query(
            models.RepositoryItem,
            votes,
            favourites,
            is_favourite,
            is_voted_positive,
            is_voted_negative
        )
        .outerjoin(models.Vote, models.Vote.repository_item_id == models.RepositoryItem.id)
        .outerjoin(models.Favourite, models.Favourite.repository_item_id == models.RepositoryItem.id)
        .group_by(models.RepositoryItem.id)
    )

    return query


def vote_up(db, repository_item_id: int):
    ''' Vote up a repository item by ID '''
    repository_item = get_by_id(db, repository_item_id)
    if repository_item:
        repository_item.votes_up += 1
        db.commit()
        db.refresh(repository_item)
    return repository_item

def vote_down(db, repository_item_id: int):
    ''' Vote down a repository item by ID '''
    repository_item = get_by_id(db, repository_item_id)
    if repository_item:
        repository_item.votes_down -= 1
        db.commit()
        db.refresh(repository_item)
    return repository_item

def favourite(db, repository_item_id: int):
    ''' Favourite a repository item by ID '''
    repository_item = get_by_id(db, repository_item_id)
    if repository_item:
        repository_item.favourites += 1
        db.commit()
        db.refresh(repository_item)
    return repository_item

def download(db, repository_item_id: int):
    ''' Increment download count for a repository item by ID '''
    repository_item = get_by_id(db, repository_item_id)
    if repository_item:
        repository_item.downloads += 1
        db.commit()
        db.refresh(repository_item)

def create(db, name: str, description: str, services: str, app_id: int, user_id: int):
    ''' Create a new store item '''
    db_repository_item = models.RepositoryItem(
        name=name,
        description=description,
        services=services,
        app_id=app_id,
        user_id=user_id
    )
    db.add(db_repository_item)
    db.commit()
    db.refresh(db_repository_item)
    return db_repository_item

def approve(db, repository_item_id: int):
    ''' Approve a repository item by ID '''
    repository_item = get_by_id(db, repository_item_id)
    if repository_item:
        repository_item.state = 'approved'
        db.commit()
        db.refresh(repository_item)
    return repository_item

def reject(db, repository_item_id: int):
    ''' Reject a repository item by ID '''
    repository_item = get_by_id(db, repository_item_id)
    if repository_item:
        repository_item.state = 'rejected'
        db.commit()
        db.refresh(repository_item)
    return repository_item

def delete(db, repository_item_id: int):
    ''' Delete a repository item by ID '''
    repository_item = get_by_id(db, repository_item_id)
    if repository_item:
        db.delete(repository_item)
        db.commit()
    return repository_item