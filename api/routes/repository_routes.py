import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.routes.auth_routes import verify_jwt
from api.schemas import repository_item 
from api.services import repository_item_service as RepositoryItemService   
repositoryRouter = APIRouter()

@repositoryRouter.get(
    "/", 
    tags=["Repository Items"], 
    description="Get all repository items", 
    response_model_exclude_none=True, 
    dependencies=[Depends(verify_jwt)]
)
async def get_repository_items(db: Session = Depends(get_db), db_user=Depends(verify_jwt)):
    return await RepositoryItemService.get_repository_items(db, db_user.id)

@repositoryRouter.get(
    "/{repository_item_id}",
    tags=["Repository Items"],
    description="Get repository item by ID",
    response_model_exclude_none=True,
    dependencies=[Depends(verify_jwt)]
)
async def get_repository_item(repository_item_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    return await RepositoryItemService.get_repository_item_by_id(db, repository_item_id, db_user.id)


@repositoryRouter.post(
    "/{repository_item_id}/vote_up",
    tags=["Repository Items"],
    description="Vote up a repository item",
    response_model_exclude_none=True,
    dependencies=[Depends(verify_jwt)]
)
async def vote_up_repository_item(repository_item_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    return await RepositoryItemService.vote_up_repository_item(db, db_user.id, repository_item_id)

@repositoryRouter.post(
    "/{repository_item_id}/vote_down",
    tags=["Repository Items"],
    description="Vote down a repository item",
    response_model_exclude_none=True,
    dependencies=[Depends(verify_jwt)]
)
async def vote_down_repository_item(repository_item_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    return await RepositoryItemService.vote_down_repository_item(db, db_user.id, repository_item_id)

@repositoryRouter.post(
        "/{repository_item_id}/favourite",
        tags=["Repository Items"],
        description="Favourite a repository item",
        response_model_exclude_none=True,
        dependencies=[Depends(verify_jwt)]
)
async def favourite_repository_item(repository_item_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    return await RepositoryItemService.favourite_repository_item(db, db_user.id, repository_item_id)

@repositoryRouter.post(
    "/{repository_item_id}/download",
    tags=["Repository Items"],
    description="Increment download count for a repository item",
    response_model_exclude_none=True,
    dependencies=[Depends(verify_jwt)]
)
async def download_repository_item(repository_item_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    return await RepositoryItemService.download_repository_item(db, db_user.id, repository_item_id)

@repositoryRouter.post(
    "/",
    tags=["Repository Items"],
    description="Create a new repository item",
    response_model_exclude_none=True,
    dependencies=[Depends(verify_jwt)]
)
async def create_repository_item(
    item: repository_item.RepositoryItemCreate, 
    db: Session = Depends(get_db)
):
    return await RepositoryItemService.create_repository_item(
        db,
        item.name,
        item.description,
        item.services,
        item.app_id,
        item.user_id
    )

@repositoryRouter.post(
    "/{repository_item_id}/approve",
    tags=["Repository Items"],
    description="Approve a repository item",
    response_model_exclude_none=True,
    dependencies=[Depends(verify_jwt)]
)
async def approve_repository_item(repository_item_id: int, db: Session = Depends(get_db)):
    return await RepositoryItemService.approve_repository_item(db, repository_item_id)

@repositoryRouter.post(
    "/{repository_item_id}/reject",
    tags=["Repository Items"],
    description="Reject a repository item",
    response_model_exclude_none=True,
    dependencies=[Depends(verify_jwt)]
)
async def reject_repository_item(repository_item_id: int, db: Session = Depends(get_db)):
    return await RepositoryItemService.reject_repository_item(db, repository_item_id)

@repositoryRouter.delete(
    "/{repository_item_id}",
    tags=["Repository Items"],
    description="Delete a repository item",
    response_model_exclude_none=True,
    dependencies=[Depends(verify_jwt)]
)
async def delete_repository_item(repository_item_id: int, db: Session = Depends(get_db)):
    return await RepositoryItemService.delete_repository_item(db, repository_item_id)
