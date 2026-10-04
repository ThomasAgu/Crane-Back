''' This module contains the services for the crane app. '''
import asyncio
import json
from fastapi import HTTPException
from python_on_whales import docker
from sqlalchemy.orm import Session
from starlette import status
import api.db.crud.app_crud as AppCrud
import api.db.crud.alert_crud as AlertCrud
from api.schemas.app import App, AppDocker, ProxyRoute
from api.clients.docker_client import get_docker_client
from api.config.constants import PROMETHEUS_NETWORK_NAME
from api.services.generator_service import docker_compose_generator, docker_compose_remove, prometheus_scrape_generator, prometheus_scrape_remove
from api.services.monitoring_service import restart_monitoring
from api.db import models, schemas
from datetime import datetime
import re

SERVICE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
CONTAINER_PATH_PATTERN = re.compile(r"^/(?:[a-zA-Z0-9._-]+/)*[a-zA-Z0-9._-]+$")
ALLOWED_RESTART_POLICIES = {"unless-stopped", "always", "on-failure", "no"}


def _read_app_container_logs(project_name):
    containers = docker.container.list(all=True)
    app_containers = [
        container for container in containers
        if container.name.startswith(f"{project_name}-")
    ]

    logs = []
    for container in app_containers:
        logs.append(container.logs(tail=500))
    return "\n".join(logs)


def _get_app_runtime_access(project_name):
    containers = docker.container.list(all=True)
    app_containers = [
        container for container in containers
        if container.name.startswith(f"{project_name}-")
    ]
    links = []
    traefik = None

    for container in app_containers:
        ports = container.network_settings.ports or {}
        if container.name.startswith(f"{project_name}-traefik"):
            http_port = next(iter(ports.get("80/tcp", [])), None)
            dashboard_port = next(iter(ports.get("8080/tcp", [])), None)
            traefik = {
                "url": f"http://localhost:{http_port['HostPort']}/" if http_port else None,
                "dashboard_url": (
                    f"http://localhost:{dashboard_port['HostPort']}/dashboard/"
                    if dashboard_port else None
                ),
                "ports": ports,
            }
            continue

        service_name = container.name[len(project_name) + 1:].rsplit("-", 2)[0]
        for container_port, published_ports in ports.items():
            for published_port in published_ports or []:
                if not published_port or not published_port.get("HostPort"):
                    continue
                links.append({
                    "name": service_name,
                    "type": "service",
                    "container_port": container_port,
                    "url": f"http://localhost:{published_port['HostPort']}/",
                })

    if traefik:
        if traefik["url"]:
            links.append({"name": "Traefik", "type": "traefik", "url": traefik["url"]})
        if traefik["dashboard_url"]:
            links.append({
                "name": "Traefik dashboard",
                "type": "traefik-dashboard",
                "url": traefik["dashboard_url"],
            })

    return links, traefik


def validate_app_configuration(app: App):
    """Validate configuration before it can create database or Docker state."""
    errors = []

    if not app.name or not app.name.strip():
        errors.append("El nombre de la aplicación es obligatorio.")
    if not app.services:
        errors.append("La aplicación debe tener al menos un servicio.")

    service_names = set()
    for index, service in enumerate(app.services):
        label = service.name or f"servicio {index + 1}"
        if not service.name or not SERVICE_NAME_PATTERN.fullmatch(service.name):
            errors.append(f"El nombre de {label} solo puede contener letras, números, '.', '_' y '-'.")
        if service.name in service_names:
            errors.append(f"El nombre de servicio '{service.name}' está repetido.")
        service_names.add(service.name)

        if not service.image or not service.image.strip():
            errors.append(f"El servicio '{label}' debe tener una imagen Docker.")
        if service.restart_policy not in ALLOWED_RESTART_POLICIES:
            errors.append(f"La política de reinicio del servicio '{label}' no es válida.")

        for volume in service.volumes or []:
            path = volume.path if hasattr(volume, "path") else str(volume)
            parts = path.split(":")
            container_path = parts[-1]
            if len(parts) > 2 or not CONTAINER_PATH_PATTERN.fullmatch(container_path):
                errors.append(f"El volumen del servicio '{label}' debe apuntar a una ruta de contenedor válida.")

        network_names = set()
        for network in service.networks or []:
            network_name = network.name if hasattr(network, "name") else ""
            if not network_name or not SERVICE_NAME_PATTERN.fullmatch(network_name):
                errors.append(f"El servicio '{label}' tiene una red con nombre inválido.")
            if network_name in network_names:
                errors.append(f"La red '{network_name}' está repetida en el servicio '{label}'.")
            network_names.add(network_name)

    if app.min_scale is not None and app.current_scale is not None and app.min_scale > app.current_scale:
        errors.append("La escala mínima no puede ser mayor que la escala actual.")
    if app.current_scale is not None and app.max_scale is not None and app.current_scale > app.max_scale:
        errors.append("La escala actual no puede ser mayor que la escala máxima.")
    if app.min_scale is not None and app.max_scale is not None and app.min_scale > app.max_scale:
        errors.append("La escala mínima no puede ser mayor que la escala máxima.")

    if errors:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=" ".join(errors))

async def create(db: Session, app: App, user_id: int):
    validate_app_configuration(app)
    app.user_id = user_id

    # 1. Crear pre-registro en la base de datos
    db_app = AppCrud.create(db, app)
    
    # Reasignamos el nombre con el ID autoincremental de la DB
    app.name = f"{db_app.name}-{db_app.id}"

    # If is template then is not necessary to generate docker-compose or start containers, just return the db_app
    if (db_app.is_template): 
        return db_app

    docker_started = False
    temp_files_generated = False    
    try:
        # 2. Intentar generar el docker-compose
        compose = docker_compose_generator(app)
        temp_files_generated = True

        # 3. Intentar levantar los contenedores con Docker
        docker = await get_docker_client(app.name)
        docker.compose.build()
        docker.compose.up(detach=True)
        docker_started = True  # Bandera por si tenemos que hacer rollback del contenedor

        # 4. Configuración de redes y proxy
        proxy_route = await get_router_dir(app.name, docker)
        db_app.hosts = compose['hosts']
        db_app.services = json.loads(db_app.services)

        # Actualizar estado exitoso en la DB
        AppCrud.update(db, db_app)

        # 5. Métricas (Prometheus)
        prometheus_scrape_generator(app.name, proxy_route.ip)

        # 6. Crear las alertas customisables de app.alerts (si vienen desde el frontend)
        alerts = getattr(app, 'alerts', []) or []
        if alerts:
            from api.services import alert_service as AlertService
            for alert in alerts:
                try:
                    await AlertService.create(db, db_app.id, alert)
                except Exception as e:
                    print(f"Failed to create alert for app {db_app.id}: {e}")

        await restart_monitoring()

    except Exception as e:
        # --- CONTROL DE ERRORES Y ROLLBACK ---
        print(f"Error detectado durante el despliegue de la App: {str(e)}")
        
        # Si los contenedores llegaron a encenderse, los apagamos y removemos
        if docker_started:
            try:
                docker.compose.down(volumes=True)
            except Exception:
                pass
        
        # Eliminar registro fallido de la DB para no ensuciar el dashboard del usuario
        try:
            AppCrud.delete(db, db_app.id)
        except Exception:
            pass

        # Elevar una excepción limpia que el controlador de FastAPI pueda entender
        raise HTTPException(
            status_code=422, 
            detail=f"Failed to build or orchestrate the app infrastructure. Error: {str(e)}"
        )
        
    finally:
        # Limpieza obligatoria de archivos temporales locales
        if temp_files_generated:
            docker_compose_remove(app.name)

    return db_app

async def copy(db: Session, app_id: int, user_id: int):
    ''' Duplicate the app row and update the user_id '''
    # Retrieve the app to be copied
    app = AppCrud.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    # Create a copy of the app
    app_copy = models.App(
        #Este nombre se repite con cada copia que hacemos jejox
        name=f"{app.name}-copia",
        services=app.services,
        hosts=app.hosts,
        current_scale=app.current_scale,
        min_scale=app.min_scale,
        max_scale=app.max_scale,
        force_stop=app.force_stop,
        user_id=user_id,
        is_template=app.is_template,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        deleted_at=None
    )

    # Add the new app to the database
    db.add(app_copy)
    db.commit()
    db.refresh(app_copy)

    # Copy custom alerts from original app to the new copy
    try:
        original_alerts = getattr(app, 'custom_alerts', []) or []
        if original_alerts:
            from api.services import alert_service as AlertService
            for a in original_alerts:
                try:
                    await AlertService.create(db, app_copy.id, a)
                except Exception as e:
                    print(f"Failed to copy alert for app {app.id}: {e}")
    except Exception:
        # Do not block the copy if alerts fail to copy
        pass

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
    validate_app_configuration(app)
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


async def delete(db: Session, app_id: int, user_id: int):
    """Delete app on db and docker compose."""
    try:
        app = await get_app_with_docker(db, app_id, user_id)
        deleted_app = AppCrud.delete_physical(db, app.id, user_id)

        app.docker.compose.down()
        docker_compose_remove(app.name)
        prometheus_scrape_remove(app.name)
        await restart_monitoring()

        return {"message": f"App {deleted_app.name} deleted"}

    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def logs(db: Session, app_id: str, user_id: int):
    ''' Get logs for app services containers '''
    app = await get_app_by_id(db, app_id, user_id, include_runtime=False)
    project_name = f"{app.name}-{app.id}"

    try:
        return await asyncio.to_thread(_read_app_container_logs, project_name)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No se pudieron obtener los logs de la aplicación: {exc}"
        ) from exc


async def stats(db: Session, app_id: str, user_id: int):
    ''' Get stats for app services containers '''
    app = await get_app_with_docker(db, app_id, user_id)
    app_stats = app.docker.stats()
    app_stats = [
        service for service in app_stats if service.container_name.startswith(app.name)
    ]
    return app_stats


async def get_app_by_id(db, app_id: int, user_id: int = None, include_runtime: bool = True):
    ''' Get app by id '''
    app = AppCrud.get_by_id(db, app_id, user_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    app.alerts = AlertCrud.get_by_app_id(db, app.id)
    if isinstance(app.services, str):
        app.services = json.loads(app.services)
    if isinstance(app.hosts, str):
        app.hosts = json.loads(app.hosts)
    if include_runtime:
        host_links, traefik = await asyncio.to_thread(
            _get_app_runtime_access, f"{app.name}-{app.id}"
        )
        app.hosts = host_links
        app.traefik = traefik
    return app

async def get_app_by_name_and_user_id(db, app_name: str, user_id: int):
    ''' Get app by name and user_id '''
    app = AppCrud.get_by_name_and_user_id(db, app_name, user_id)

    if not app:
        return None

    app.alerts = AlertCrud.get_by_app_id(db, app.id)
    if isinstance(app.services, str):
        app.services = json.loads(app.services)
    if isinstance(app.hosts, str):
        app.hosts = json.loads(app.hosts)
    return app

async def get_app_with_docker(db, app_id: int, user_id: int = None):
    ''' Get app by id with docker client '''
    app = await get_app_by_id(db, app_id, user_id, include_runtime=False)
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
        repository_item = AppCrud.get_by_id(db, app.id, user_id).repository_item
        app_data = {
            **app.__dict__,
            "repository_state": repository_item.state if repository_item else None,
            "repository_updated_at": (
                (repository_item.updated_at or repository_item.created_at)
                if repository_item else None
            ),
        }
        app_name = f"{app.name}-{app.id}"
        docker_app = AppDocker(**app_data)
        docker_compose_generator(docker_app)
        proxy_route = await get_router_dir(app_name, await get_docker_client(app.id))
        docker_app.ip = proxy_route.ip
        docker_app.ports = proxy_route.ports
        docker_app.status = proxy_route.status
        docker_app.host_links, docker_app.traefik = await asyncio.to_thread(
            _get_app_runtime_access, app_name
        )
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
        if isinstance(app.services, str):
            app.services = json.loads(app.services)
        if isinstance(app.hosts, str):
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
    
    # Buscamos el contenedor de traefik de manera segura usando un generador
    proxy_container = next(
        (c for c in containers if c.name.startswith(f"{app_name}-traefik")), 
        None
    )
    
    # Si encontramos contenedores de la app, pero ninguno es el proxy de Traefik
    if not proxy_container:
        return ProxyRoute(
            ip=None,
            ports=None,
            status="Degraded"  # O "Running" / "Stopped" según consideres tu arquitectura
        )
        
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
