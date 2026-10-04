from sqlalchemy.orm import Session
from api.db import models, schemas

def create(db: Session, scenario: schemas.ScenarioCreate):
  '''Create hardcoded scenarios'''
  scenario_data = scenario.dict()
  db_scenario = models.Scenario(**scenario_data)
  db.add(db_scenario)
  db.commit()
  db.refresh(db_scenario)

def get_all(db: Session, skip: int = 0, limit: int = 100):
  '''Get all scenarios'''
  return db.query(models.Scenario).limit(limit).all()

def get_by_id(db: Session, scenario_id: int):
  '''Get scenario by id'''
  return db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()