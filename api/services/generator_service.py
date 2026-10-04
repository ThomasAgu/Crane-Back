''' This module contains the functions to CRUD the docker-compose and prometheus yaml files'''
import os
import shutil
import copy
from pathlib import Path
import yaml
from fastapi.responses import JSONResponse
from api.config.proxy import get_config
from api.schemas.app import App
from api.config.constants import (TEMP_FILES_PATH, GLOBAL_SCRAPE_INTERVAL, GLOBAL_EVALUATION_INTERVAL,
                                  EXTERNAL_LABELS_MONITOR, RULES_FILE, ALERT_MANAGER_SCHEME, ALERT_MANAGER_PORT,
                                  PROMETHEUS_SCRAPE_INTERVAL, PROMETHEUS_PORT, TARGET_PORT, MONITORING_FILES_PATH,
                                  PROMETHEUS_FILE, REMOVE_TEMP_FILES, PROMETHEUS_SCRAPE_JOB_NAME)
from api.db.models import CustomAlert
from sqlalchemy.orm import Session

def write_yaml(obj, path):
    ''' Write yaml file '''
    with open(path, "w", encoding="utf-8") as file:
        yaml.dump_all(obj, file)


def docker_compose_generator(app: App):
    ''' Generate docker-compose.yml file '''
    import copy
    from pathlib import Path
    
    app = copy.deepcopy(app)
    proxy = get_config(app.name)

    if not proxy:
        raise ValueError("Wrong proxy config detected")

    # Carpeta base para esta aplicación en particular
    app_dir = Path.cwd() / TEMP_FILES_PATH / app.name

    yaml_obj = [
        {
            "networks": {
                "prometheus-net": {"external": True},
                "crane-net": {}
            },
            'services': {
                proxy['name']: {
                    'image': proxy['image'],
                    'command': proxy['command'],
                    'ports': proxy['ports'],
                    'volumes': proxy['volumes'],
                    'networks': proxy['networks']
                }
            }
        }
    ]
    
    app_hosts = []

    for service in app.services:
        srv_dict = service.model_dump(by_alias=True)
        name = srv_dict.pop('name', None)
        
        # 1. Mapeo y Saneamiento de Volúmenes del Usuario
        volumes_raw = srv_dict.pop('volumes', [])
        service_volumes = []
        for v in volumes_raw:
            path_str = v.get('path', '')
            # Validamos que el binding contenga el separador básico de docker ':'
            if ":" in path_str and not path_str.startswith("/:/:"):
                service_volumes.append(path_str)
        
        # 2. PROCESAMIENTO DE SCRIPTS INICIALES (Startup Scripts)
        startup_scripts = srv_dict.pop('startup_scripts', [])
        if startup_scripts:
            # Creamos un subdirectorio exclusivo para guardar los scripts de este servicio
            scripts_dir = app_dir / "scripts" / name
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            for script in startup_scripts:
                script_name = script.get('name')
                script_content = script.get('content', '')
                
                if script_name:
                    file_path = scripts_dir / script_name
                    # Guardamos el script físicamente en el disco local del host
                    file_path.write_text(script_content, encoding="utf-8")
                    
                    # Lo montamos en la raíz del directorio de trabajo de la app (/app)
                    # Ej: /absolute/path/to/temp/app-1/scripts/service1/index.js:/app/index.js
                    service_volumes.append(f"{file_path.absolute()}:/app/{script_name}")

        # 3. Mapeo de Redes
        networks_raw = srv_dict.pop('networks', [])
        service_networks = []
        for net in networks_raw:
            net_name = net['name'].replace(" ", "_")
            service_networks.append(net_name)
            if net_name not in yaml_obj[0]['networks']:
                yaml_obj[0]['networks'][net_name] = {"driver": "bridge"}

        if "crane-net" not in service_networks:
            service_networks.append("crane-net")

        # 4. Etiquetas (Labels) de Traefik
        labels = srv_dict.get('labels', [])
        labels.extend([
            f"a.label.name={app.name}", 
            f"traefik.http.routers.{app.name}-{name}.rule=Host(`{app.name}-{name}.docker.localhost`)"
        ])
        app_hosts.append(f"{app.name}-{name}.docker.localhost")

        # 5. Estructurar el diccionario del servicio
        restart_policy = srv_dict.pop('restart_policy', 'unless-stopped')
        
        docker_service_config = {
            'image': srv_dict.get('image'),
            'networks': service_networks,
            'labels': labels,
            'restart': restart_policy,
            # Le asignamos la carpeta /app como espacio de ejecución para Node
            'working_dir': '/app' 
        }

        # Soporte nativo para el command ("node index.js")
        if srv_dict.get('command'):
            docker_service_config['command'] = srv_dict['command']

        if srv_dict.get('ports'):
            docker_service_config['ports'] = srv_dict['ports']

        if service_volumes:
            docker_service_config['volumes'] = service_volumes

        if srv_dict.get('environment'):
            docker_service_config['environment'] = srv_dict['environment']

        if srv_dict.get('resources') and srv_dict['resources'].get('limits'):
            limits = srv_dict['resources']['limits']
            clean_limits = {k: v for k, v in limits.items() if v is not None}
            if clean_limits:
                docker_service_config['deploy'] = {'resources': {'limits': clean_limits}}

        yaml_obj[0]['services'][name] = docker_service_config

    # Guardar el compose definitivo en disco
    path = app_dir / "docker-compose.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(yaml_obj, path)

    return {
        "hosts": app_hosts,
        "path": path,
        "yaml": yaml_obj
    }


def docker_compose_remove(app_path_name: str):
    ''' Remove docker-compose.yml file '''
    if REMOVE_TEMP_FILES:
        path = Path.cwd() / TEMP_FILES_PATH / app_path_name
        shutil.rmtree(path)
        return "App removed"
    else:
        return "App not removed because REMOVE_TEMP_FILES is False"


def prometheus_yaml_generator(force=False):
    ''' Generate prometheus.yml file '''
    yaml_obj = [
        {

            "global": {
                "scrape_interval": GLOBAL_SCRAPE_INTERVAL,
                "evaluation_interval": GLOBAL_EVALUATION_INTERVAL,
                "external_labels": {
                    "monitor": EXTERNAL_LABELS_MONITOR
                }
            },
            "rule_files": [
                "/etc/prometheus/rules/*.yml"
            ],
            "alerting": {
                "alertmanagers": [
                    {
                        "scheme": ALERT_MANAGER_SCHEME,
                    },
                    {
                        "static_configs": [
                            {
                                "targets": [
                                    f"alertmanager:{ALERT_MANAGER_PORT}"
                                ]
                            }
                        ]
                    }
                ]
            },
            "scrape_configs": [
                {
                    "job_name": PROMETHEUS_SCRAPE_JOB_NAME,
                    "static_configs": [
                        {
                            "targets": [
                                f"localhost:{PROMETHEUS_PORT}"
                            ]
                        }
                    ]
                }
            ]
        }
    ]
    if not force:
        if os.path.exists(f"{os.getcwd()}/{MONITORING_FILES_PATH}/prometheus/{PROMETHEUS_FILE}"):
            return "Prometheus file already exists"

    os.makedirs(
        f'{os.getcwd()}/{MONITORING_FILES_PATH}/prometheus',
        exist_ok=True
    )

    path = Path.cwd() / MONITORING_FILES_PATH / "prometheus" / PROMETHEUS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(yaml_obj, path)

    return yaml_obj


def prometheus_scrape_generator(app_name: str, app_ip: str):
    ''' Generate prometheus.yml file '''
    with open(f"{MONITORING_FILES_PATH}/prometheus/{PROMETHEUS_FILE}", "r", encoding="utf-8") as file_to_read:
        file_data = yaml.safe_load(file_to_read)
        search = [scrape for scrape in file_data['scrape_configs'] if scrape['job_name'] == app_name]
        if not search:
            file_data['scrape_configs'].append({
                "job_name": app_name,
                "scrape_interval": PROMETHEUS_SCRAPE_INTERVAL,
                "static_configs": [
                    {
                        "targets": [
                            f"{app_ip}:{TARGET_PORT}"
                        ]
                    }
                ]
            })
            file_to_read.close()
        else:
            search[0]['static_configs'][0]['targets'] = [f"{app_ip}:{TARGET_PORT}"]
            file_to_read.close()

    with open(f"{MONITORING_FILES_PATH}/prometheus/{PROMETHEUS_FILE}", "w", encoding="utf-8") as file_to_write:
        yaml.dump(file_data, file_to_write)
        file_to_write.close()

    return file_data


def prometheus_scrape_remove(app_name: str):
    ''' Remove prometheus scrape config '''
    with open(f"{MONITORING_FILES_PATH}/prometheus/{PROMETHEUS_FILE}", "r", encoding="utf-8") as file_to_read:
        file_data = yaml.safe_load(file_to_read)
        file_data['scrape_configs'] = [
            scrape for scrape in file_data['scrape_configs'] if scrape['job_name'] != app_name]
        file_to_read.close()
    with open(f"{MONITORING_FILES_PATH}/prometheus/{PROMETHEUS_FILE}", "w", encoding="utf-8") as file_to_write:
        yaml.dump(file_data, file_to_write)
        file_to_write.close()

    return file_data


def generate_app_rules_yml(app_id: int, db: Session):
    ''' Generate YAML file for application-specific Prometheus rules '''
    alerts = db.query(CustomAlert).filter(CustomAlert.app_id == app_id).all()

    if not alerts:
        return f"No alerts found for app_id {app_id}"

    rules = []
    for alert in alerts:
        rules.append({
            "alert": alert.alert,
            "expr": alert.expr,
            "for": alert.for_time,
            "labels": {
                "severity": alert.severity,
                "job": f"app-{alert.app_id}"
            },
            "annotations": {
                "summary": alert.summary,
                "description": alert.description
            }
        })

    yaml_obj = [{"groups": [{"name": f"app-{app_id}-rules", "rules": rules}]}]

    path = Path.cwd() / MONITORING_FILES_PATH / "rules" / f"app_{app_id}.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(yaml_obj, path)

    return {
        "path": str(path),
        "yaml": yaml_obj
    }
