from api.db.models import CustomAlert
from api.schemas.alert import CustomAlert as CustomAlertSchema

def get_by_id(db, alert_id: int, skip: int = 0, limit: int = 1):
  ''' Get a cutstom alert by id '''
  return db.query(CustomAlert).filter(CustomAlert.id == alert_id).first()

def get_by_app_id(db, app_id: int, skip: int = 0, limit: int = 100):
  ''' get custom alerts given an app_id '''
  return db.query(CustomAlert).filter(CustomAlert.app_id == app_id).all()

def create(db, app_id, alert): 
  new_alert = CustomAlert(
            app_id=app_id,
            alert=alert.alert,
            expr=alert.expr,
            for_time=alert.for_time,
            severity=alert.severity,
            summary=alert.summary,
            description=alert.description
  )

  db.add(new_alert)
  db.commit()
  db.refresh(new_alert)
  return new_alert

def delete(db, alert_id: int):
  customAlert = get_by_id(db, alert_id) 
  
  if customAlert:
      db.delete(customAlert)
      db.commit()

  return customAlert

def update(
  db,
  custom_alert: CustomAlert,
  alert: CustomAlertSchema
):
  custom_alert.alert = alert.alert
  custom_alert.expr = alert.expr
  custom_alert.for_time = alert.for_time
  custom_alert.severity = alert.severity
  custom_alert.summary = alert.summary
  custom_alert.description = alert.description
  
  db.commit()
  db.refresh(custom_alert)

  return custom_alert