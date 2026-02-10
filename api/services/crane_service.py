''' This module contains the services for the crane app. '''
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
import api.db.crud.app_crud as AppCrud
from api.schemas.app import App, AppDocker, ProxyRoute
from api.clients.docker_client import get_docker_client
from api.config.constants import PROMETHEUS_NETWORK_NAME
from api.services.generator_service import docker_compose_generator, docker_compose_remove, prometheus_scrape_generator, prometheus_scrape_remove
from api.services.monitoring_service import restart_monitoring
from api.db import models, schemas
from datetime import datetime


async def create(db: Session, app: App, user_id: int):
    ''' 
        This function creates a new app in the database, 
        generates the docker-compose.yml file and starts the app. 
    '''
    # get user id
    app.user_id = user_id

    # create app in db
    db_app = AppCrud.create(db, app)

    # generate app name with selected name and id
    app.name = f"{db_app.name}-{db_app.id}"

    # create docker compose file and start app
    compose = docker_compose_generator(app)
    docker = await get_docker_client(app.name)
    docker.compose.build()
    docker.compose.up(detach=True)

    # get proxy container ip and ports
    proxy_route = await get_router_dir(app.name, docker)
    db_app.hosts = compose['hosts']
    db_app.services = json.loads(db_app.services)

    # update app in db
    AppCrud.update(db, db_app)

    # create prometheus yaml file
    prometheus_scrape_generator(app.name, proxy_route.ip)

    # restart monitoring docker compose
    await restart_monitoring()

    # remove temp files
    docker_compose_remove(app.name)

    # finally return app
    return db_app

async def copy(db: Session, app_id: int, user_id: int):
    ''' Duplicate the app row and update the user_id '''
    # Retrieve the app to be copied
    app = AppCrud.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    # Create a copy of the app
    app_copy = models.App(
        name=f"{app.name}-copia",
        services=app.services,
        hosts=app.hosts,
        current_scale=app.current_scale,
        min_scale=app.min_scale,
        max_scale=app.max_scale,
        force_stop=app.force_stop,
        user_id=user_id,  # Assign the new user as the creator
        created_at=datetime.now(),
        updated_at=datetime.now(),
        deleted_at=None
    )

    # Add the new app to the database
    db.add(app_copy)
    db.commit()
    db.refresh(app_copy)

    return app_copy

    # Add the new app to the database
    AppCrud.create(db, app_copy)

    return app_copy


async def start(db: Session, app_id: str, user_id: int = None):
    ''' Start docker compose for app '''
    app = await get_app_with_docker(db, app_id, user_id)
    app.docker.compose.build()
    app.docker.compose.up(detach=True)
    docker_compose_remove(app.name)
    return {"message": f"App {app.name} started"}


async def scale(db: Session, app_id: str, count: int, user_id: int = None):
    ''' Scale app services '''
    app = await get_app_with_docker(db, app_id, user_id)
    scales = {service['name']: count for service in app.services}
    app.docker.compose.up(detach=True, scales=scales)
    return {"message": f"App {app.name} scaled"}


async def update(db: Session, app_id: str, app: App, user_id: int):
    ''' Update app on db and docker compose '''
    db_app = await get_app_by_id(db, app_id, user_id)
    db_app.services = app.services
    db_app.min_scale = app.min_scale
    db_app.current_scale = app.current_scale
    db_app.max_scale = app.max_scale
    db_app.force_stop = app.force_stop
    db_app.hosts = app.hosts
    AppCrud.update(db, db_app)
    return {"message": f"App {app.name} updated"}


async def restart(db: Session, app_id: str, user_id: int):
    ''' Restart app services '''
    app = await get_app_with_docker(db, app_id, user_id)
    app.docker.compose.restart()
    return {"message": f"App {app.name} restarted"}


async def stop(db: Session, app_id: str, user_id: int):
    ''' Stop app services '''
    app = await get_app_with_docker(db, app_id, user_id)
    app.docker.compose.stop()
    docker_compose_remove(app.name)
    return {"message": f"App {app.name} stopped"}


async def delete(db: Session, app_id: str, user_id: int):
    ''' Delete app on db and docker compose '''
    app = await get_app_with_docker(db, app_id, user_id)
    app.docker.compose.down()
    docker_compose_remove(app.name)
    prometheus_scrape_remove(app.name)
    await restart_monitoring()
    AppCrud.delete_physical(db, app.name, user_id)
    return {"message": f"App {app.name} deleted"}


async def logs(db: Session, app_id: str, user_id: int):
    ''' Get logs for app services containers '''
    app = await get_app_with_docker(db, app_id, user_id)
    return app.docker.compose.logs()


async def stats(db: Session, app_id: str, user_id: int):
    ''' Get stats for app services containers '''
    app = await get_app_with_docker(db, app_id, user_id)
    app_stats = app.docker.stats()
    app_stats = [
        service for service in app_stats if service.container_name.startswith(app.name)
    ]
    return app_stats


async def get_app_by_id(db, app_id: int, user_id: int = None):
    ''' Get app by id '''
    app = AppCrud.get_by_id(db, app_id, user_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    app.services = json.loads(app.services)
    app.hosts = json.loads(app.hosts)
    return app


async def get_app_with_docker(db, app_id: int, user_id: int = None):
    ''' Get app by id with docker client '''
    app = await get_app_by_id(db, app_id, user_id)
    app = AppDocker(**app.__dict__)
    app.name = app.name + "-" + str(app.id)
    docker_compose_generator(app)
    app.docker = await get_docker_client(app.name)
    return app


async def get_apps_with_docker(db, user_id: int = None, skip: int = 0, limit: int = 100):
    ''' Get all apps with docker status info   '''
    apps = await get_all(db, user_id, skip, limit)
    docker_apps = []
    for app in apps:
        app_name = f"{app.name}-{app.id}"
        docker_app = AppDocker(**app.__dict__)
        docker_compose_generator(docker_app)
        proxy_route = await get_router_dir(app_name, await get_docker_client(app.id))
        docker_app.ip = proxy_route.ip
        docker_app.ports = proxy_route.ports
        docker_app.status = proxy_route.status
        docker_apps.append(docker_app)
    return docker_apps


async def get_app_by_name(db, app_name: str, user_id: int):
    ''' Get app by name '''
    app = AppCrud.get_by_name(db, app_name, user_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    app.services = json.loads(app.services)
    app = {k: v for k, v in app.__dict__.items() if v is not None}
    return app


async def get_all(db, user_id: int, skip: int = 0, limit: int = 100):
    ''' Get all apps '''
    apps = AppCrud.get_all(db, user_id, skip, limit)
    for app in apps:
        app.services = json.loads(app.services)
        app.hosts = json.loads(app.hosts)

    return apps


async def get_router_dir(app_name: str, docker):
    ''' Get proxy container ip and ports '''
    containers = docker.ps(filters={"name": app_name})
    if not containers:
        return ProxyRoute(
            ip=None,
            ports=None,
            status="Stopped"
        )
    proxy_container = [container for container in containers if container.name.startswith(app_name + "-traefik")][0]
    return ProxyRoute(
        ip=proxy_container.network_settings.networks[PROMETHEUS_NETWORK_NAME].ip_address,
        ports=proxy_container.network_settings.ports,
        status="Running"
    )


async def refresh_apps_scrapes(db: Session):
    ''' Refresh apps prometheus scrapes '''
    apps = await get_apps_with_docker(db)
    for app in apps:
        app_name = f"{app.name}-{app.id}"
        prometheus_scrape_generator(app_name, app.ip)

    await restart_monitoring()
    return {"message": "Apps refreshed"}
