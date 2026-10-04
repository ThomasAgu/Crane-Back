''' Actions routes '''
from fastapi import Depends, APIRouter 
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.db.crud.action_crud import get_all

actionRouter = APIRouter()

@actionRouter.get("/", tags=["Action"], description="Get actions to reproduce on alerts")
def get_all_actions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
  return get_all(db=db, skip=skip, limit=limit)         