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

    app = copy.deepcopy(app)
    proxy = get_config(app.name)

    if not proxy:
        return JSONResponse(status_code=400, content={"message": "Wrong proxy config detected", "proxy": proxy})

    yaml_obj = [
        {
            "networks": {
                "prometheus-net": {
                    "external": True
                },
                "crane-net": {}
            },
            'services': {
                proxy['name']:
                {
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
    services = app.services

    for service in services:
        name = service.pop('name', None)
        labels = service.get('labels', [])
        labels.extend([f"a.label.name={app.name}", f"traefik.http.routers.{app.name}.rule=Host(`{app.name}-{name}.docker.localhost`)"])
        app_hosts.append(f"{app.name}-{name}.docker.localhost")
        service['labels'] = labels
        yaml_obj[0]['services'][name] = service

    path = Path.cwd() / TEMP_FILES_PATH / app.name / "docker-compose.yml"
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
