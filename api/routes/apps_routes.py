from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from api.schemas.app import App
from api.db.database import get_db
from api.routes.auth_routes import verify_jwt
import api.services.crane_service as CraneService


appRouter = APIRouter()


@appRouter.get("/", tags=["Apps"], description="Get all user apps", response_model_exclude_none=True)
async def get(db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    apps = await CraneService.get_apps_with_docker(db, db_user.id)
    return apps


@appRouter.post("/", tags=["Apps"], description="Create a new app")
async def create(app: App, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    appExist = await CraneService.get_app_by_name_and_user_id(db, app.name, db_user.id)
    if appExist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="App with this name already exists")
    
    app = await CraneService.create(db, app, db_user.id)
    return app


@appRouter.patch("/{app_id}", tags=["Apps"], description="Update an app")
async def update(app_id: str, app: App, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    app = await CraneService.update(db, app_id, app, db_user.id)
    return app


@appRouter.get("/{app_id}", tags=["Apps"], description="Get an app", response_model_exclude_none=True)
async def get_app(app_id: str, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    app = await CraneService.get_app_by_id(db, app_id, db_user.id)
    return app


@appRouter.delete("/{app_id}", tags=["Apps"], description="Delete an app")
async def delete(app_id: str, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    app = await CraneService.delete(db, app_id, db_user.id)
    return app


@appRouter.post("/{app_id}/start", tags=["Apps"], description="Start services of the app ")
async def start(app_id: str, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    app = await CraneService.start(db, app_id, db_user.id)
    return app


@appRouter.post("/{app_id}/stop", tags=["Apps"], description="Stop services of the app")
async def stop(app_id: int, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    app = await CraneService.stop(db, app_id, db_user.id)
    return app


@appRouter.post("/{app_id}/scale", tags=["Apps"], description="Generate a new instance of the app services")
async def scale(app_id: str, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    app = await CraneService.scale(db, app_id, db_user.id)
    return app


@appRouter.post("/{app_id}/restart", tags=["Apps"], description="Restart services of the app")
async def restart(app_id: str, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    app = await CraneService.restart(db, app_id, db_user.id)
    return app


@appRouter.post("/{app_id}/logs", tags=["Apps"], description="Get logs for app")
async def logs(app_id: str, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    app_logs = await CraneService.logs(db, app_id, db_user.id)
    return app_logs


@appRouter.post("/{app_id}/stats", tags=["Apps"], description="Get stats for app")
async def stats(app_id: str, db_user=Depends(verify_jwt), db: Session = Depends(get_db)):
    app_stats = await CraneService.stats(db, app_id, db_user.id)
    return app_stats


@appRouter.post("/refresh", tags=["Apps"], description="Refresh apps scrapes on prometheus yaml and database", dependencies=[Depends(verify_jwt)])
async def refresh(db: Session = Depends(get_db)):
    apps = await CraneService.refresh_apps_scrapes(db)
    return apps
