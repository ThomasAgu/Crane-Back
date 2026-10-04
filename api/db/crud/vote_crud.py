from api.db import models

def get_by_user_id_and_app_id(db, user_id: int, app_id: int):
    ''' Get repository item by user ID and app ID '''
    return db.query(models.Vote).filter(
        models.Vote.user_id == user_id,
            models.Vote.repository_item_id == app_id
        ).first()

def add_vote(db, user_id: int, repository_item_id: int, vote_type: str):
    ''' Add a vote (up or down) to a repository item by ID '''
    existing_vote = get_by_user_id_and_app_id(db, user_id, repository_item_id)
    vote_type = vote_type.lower()

    if existing_vote and existing_vote.vote_type == vote_type:
        db.delete(existing_vote)
        db.commit()
        return 
    
    if existing_vote:
        existing_vote.vote_type = vote_type
        db.commit()
        return

    vote = models.Vote(
        user_id=user_id,
        repository_item_id=repository_item_id,
        vote_type=vote_type
    )
    db.add(vote)
    db.commit()