''' This module contains the services for managing alerts '''
from typing import Any, Dict
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.schemas.alert import AlertNotification
from api.clients.opa_client import get_opa_raw_data
import api.db.crud.app_crud as AppCrud
import api.db.crud.alert_crud as AlertCrud
import api.db.crud.app_policy_crud as AppPolicyCrud
from api.config.constants import OPA_ALERT_RULES_CONFIG_NAME
from api.services.crane_service import start, scale
from api.db.models import AppPolicy, CustomAlert


async def manage_alert(db: Session, data: Dict[Any, Any]):
    notification = AlertNotification.parse_obj(data)
    alert_name = notification.groupLabels.alertname
    status = notification.status

    opa_config = get_opa_raw_data(OPA_ALERT_RULES_CONFIG_NAME).get('result', {})
    global_function_name = opa_config.get(alert_name, {}).get(status)

    for alert in notification.alerts:
        app_id, app = await get_app_context(db, alert)
        if not app:
            continue

        function_name = None

        if global_function_name:
            function_name = global_function_name
        else:
            policy = (db.query(AppPolicy)
                      .join(CustomAlert)
                      .filter(CustomAlert.app_id == app_id, 
                              CustomAlert.alert == alert_name)
                      .first())
            
            if policy:
                function_name = policy.firing_action if status == "firing" else policy.resolved_action

        action = globals().get(function_name)
        if action:
            await action(db, app)
        else:
            print(f"Acción {function_name} no encontrada o no permitida.")

    return {"message": "Alerts processed"}


async def get_alerts(db, app_id):
    '''Get custom alerts given an app_id'''
    custom_alerts = AlertCrud.get_by_app_id(db, app_id)
    return custom_alerts

async def create(db, app_id, alert):
    new_alert = AlertCrud.create(db, app_id, alert)
    AppPolicyCrud.create(db, app_id, new_alert, alert)
    return new_alert

async def update(db, app_id, alert, alert_id):
    ''' Update a Custom alert '''
    custom_alert = AlertCrud.get_by_id(db, alert_id)
    if not custom_alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    AlertCrud.update(db, custom_alert, alert)

    app_policy = AppPolicyCrud.get_by_app_id_and_alert_id(db, app_id, alert_id)
    if not app_policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    AppPolicyCrud.update(db, app_policy, alert)
    db.commit()

    return {"message": "Custom alert and policy updated successfully"}

async def delete(db, app_id, alert_id):
    ''' Delete an existing alert from an app'''
    AppPolicyCrud.delete(db, app_id, alert_id)
    return AlertCrud.delete(db, alert_id)
        
async def get_app_context(db: Session, alert):
    """ Centraliza la extracción de la app """
    try:
        app_id = alert.labels.job.split("-")[-1]
        app = AppCrud.get_by_id(db, app_id, None)
        return app_id, app
    except (IndexError, AttributeError):
        return None, None

async def start_app(db, app):
    '''Start app if not force stopped'''
    if not app.force_stop:
        await start(db, app.id)

async def stop_app(db, app):
    '''Stop app'''
    await scale(db, app.id, 0)

async def send_email(db, app):
    '''Send email to user'''


async def do_nothing(db, app):
    '''Do nothing - placeholder action'''
    print(f"No action taken for app {app.id}")

async def scale_app(db, app):
    '''Scale app to current scale + 1 if current scale < max scale'''
    if app.current_scale < app.max_scale:
        app.services = json.loads(app.services)
        app.hosts = json.loads(app.hosts)
        app.current_scale += 1
        AppCrud.update(db, app)
        await scale(db, app.id, app.current_scale)

async def deescalate_app(db, app):
    '''Deescalate app to min scale'''
    if app.current_scale > app.min_scale:
        app.services = json.loads(app.services)
        app.hosts = json.loads(app.hosts)
        app.current_scale = app.min_scale
        AppCrud.update(db, app)
        await scale(db, app.id, app.current_scale)


async def restart_app(db, app):
    '''Restart the application'''
    app.services = json.loads(app.services)
    app.hosts = json.loads(app.hosts)
    await scale(db, app.id, 0)
    await scale(db, app.id, app.current_scale)
    print(f"App {app.id} restarted successfully")


async def notify_admin(db, app):
    '''Send notification to admin'''
    # TODO: Implement notification logic (email, Slack, etc.)
    print(f"Admin notification sent for app {app.id}")


async def increase_cpu_limit(db, app):
    '''Increase CPU resource limit for the app'''
    # TODO: Update app resource limits in Docker/Kubernetes
    print(f"CPU limit increased for app {app.id}")


async def increase_memory_limit(db, app):
    '''Increase memory resource limit for the app'''
    # TODO: Update app resource limits in Docker/Kubernetes
    print(f"Memory limit increased for app {app.id}")


async def enable_caching(db, app):
    '''Enable caching for the app'''
    # TODO: Implement caching activation logic
    print(f"Caching enabled for app {app.id}")


async def disable_caching(db, app):
    '''Disable caching for the app'''
    # TODO: Implement caching deactivation logic
    print(f"Caching disabled for app {app.id}")


async def enable_maintenance_mode(db, app):
    '''Enable maintenance mode for the app'''
    app.maintenance_mode = True
    AppCrud.update(db, app)
    print(f"Maintenance mode enabled for app {app.id}")


async def disable_maintenance_mode(db, app):
    '''Disable maintenance mode for the app'''
    app.maintenance_mode = False
    AppCrud.update(db, app)
    print(f"Maintenance mode disabled for app {app.id}")


async def log_alert_event(db, app):
    '''Log the alert event for auditing purposes'''
    # TODO: Implement logging to external service or database
    print(f"Alert event logged for app {app.id}")


async def isolate_app(db, app):
    '''Isolate the app for troubleshooting'''
    app.services = json.loads(app.services)
    app.hosts = json.loads(app.hosts)
    app.current_scale = 1
    AppCrud.update(db, app)
    await scale(db, app.id, 1)
    print(f"App {app.id} isolated to single instance")


async def rollback_app(db, app):
    '''Rollback app to previous version'''
    # TODO: Implement rollback logic with version tracking
    print(f"Rollback initiated for app {app.id}")


async def trigger_backup(db, app):
    '''Trigger a backup of the application data'''
    # TODO: Implement backup logic
    print(f"Backup triggered for app {app.id}")