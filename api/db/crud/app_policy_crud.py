from sqlalchemy.orm import Session
from api.db.models import AppPolicy

def get_by_app_id_and_alert_id(db, app_id: int, alert_id: int):
  return db.query(AppPolicy).filter(
        (AppPolicy.app_id == app_id) &
        (AppPolicy.alert_id == alert_id)
    ).first()

def create(db, app_id, new_alert, alert):
  new_policy = AppPolicy(
    app_id=app_id,
    alert_id=new_alert.id,
    firing_action=alert.firing_action,
    resolved_action=alert.resolved_action
  )

  db.add(new_policy)
  db.commit()
  return new_policy

def delete(db, app_id: int, alert_id: int):
  app_policy = get_by_app_id_and_alert_id(db, app_id, alert_id) 
  
  if app_policy:
    db.delete(app_policy)
    db.commit()
  
  return app_policy

def update(db, app_policy, alert):
  app_policy.firing_action = alert.firing_action
  app_policy.resolved_action = alert.resolved_action

  db.commit()
  db.refresh(app_policy)

  return app_policy