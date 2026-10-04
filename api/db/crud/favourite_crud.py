from api.db import models

def get_all(db, skip: int = 0, limit: int = 100):
    ''' Get all repositems '''
    return db.query(models.RepositoryItem).offset(skip).limit(limit).all()

def get_by_user_id_and_repository_item_id(db, user_id: int, repository_item_id: int):
    ''' Get favourite by user ID and repository item ID '''
    return db.query(models.Favourite).filter(
        models.Favourite.user_id == user_id,
        models.Favourite.repository_item_id == repository_item_id
    ).first()

def add_favourite(db, user_id: int, repository_item_id: int):
    ''' Add a repository item to user's favourites '''
    existing_favourite = get_by_user_id_and_repository_item_id(db, user_id, repository_item_id)

    if existing_favourite:
        remove_favourite(db, user_id, repository_item_id)
        return 
 
    favourite = models.Favourite(
        user_id=user_id,
        repository_item_id=repository_item_id
    )
    db.add(favourite)
    db.commit()
    db.refresh(favourite)

def remove_favourite(db, user_id: int, repository_item_id: int):
    ''' Remove a repository item from user's favourites '''
    favourite = get_by_user_id_and_repository_item_id(db, user_id, repository_item_id)
    
    if favourite:
        db.delete(favourite)
        db.commit()
    return favourite