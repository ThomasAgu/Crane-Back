from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import api.services.user_service as UserService
import api.services.role_service as RoleService
from api.routes.auth_routes import verify_jwt
from api.db.database import get_db

userRouter = APIRouter()


@userRouter.get("/", tags=["Users"], description="Get user lists", dependencies=[Depends(verify_jwt)])
async def get(db: Session = Depends(get_db)):
    return await UserService.get_users_with_roles(db)

@userRouter.get("/{user_id}", tags=["Users"], description="Get user by ID")
async def get_user(user_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    user = await UserService.get_by_id(db, user_id)
    return user

@userRouter.post("/disable/{user_id}", tags=["Users"], description="Disable a user by ID", dependencies=[Depends(verify_jwt)])
async def disable_user(user_id: int, db: Session = Depends(get_db)):
    user = await UserService.disable_user(db, user_id)
    return user

@userRouter.post("/enable/{user_id}", tags=["Users"], description="Enable a user by ID", dependencies=[Depends(verify_jwt)])
async def enable_user(user_id: int, db: Session = Depends(get_db)):
    user = await UserService.enable_user(db, user_id)
    return user