''' Scenario routes '''
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.services.scenario_service import get_scenarios, manage_scenario

scenarioRouter = APIRouter()

@scenarioRouter.get('/', tags=['Scenario'], description='Get scenarios to try')
async def get_all_scenarios(db: Session = Depends(get_db)):
  return await get_scenarios(db)

@scenarioRouter.post('/{scenario_id}/app/{app_id}', tags=['Scenario'], description='Test scenario')
async def test_scenario(scenario_id: int, app_id: int, db: Session = Depends(get_db)):
  return await manage_scenario(db, scenario_id, app_id)