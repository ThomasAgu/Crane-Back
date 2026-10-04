''' This module containes the services for managing scenarios '''
from fastapi import HTTPException
import api.db.crud.scenario_crud as ScenarioCrud
import api.db.crud.app_crud as AppCrud
from sqlalchemy.orm import Session 

from api.services.testing.execution_manager import ExecutionManager

_manager = ExecutionManager(
    alertmanager_url="http://alertmanager:9093/api/v2/alerts",
    alert_poll_interval=5,
)
 
async def get_scenarios(db):
  ''' Get all scenarios '''
  return ScenarioCrud.get_all(db)

async def manage_scenario(db: Session, scenario_id: int, app_id: int) -> dict:
    """
    Orquesta la ejecución de un escenario sobre una app.
 
    Args:
        db:          sesión de base de datos.
        scenario_id: ID del escenario a ejecutar.
        app_id:      ID de la app sobre la que correr el escenario.
 
    Returns:
        dict con el reporte completo del escenario.
    """
    # Resolver escenario
    scenario = ScenarioCrud.get_by_id(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
 
    # Resolver app
    app = AppCrud.get_by_id(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
 
    # Ejecutar y obtener reporte
    report = await _manager.execute(scenario, app)
 
    # Devolver el dict estructurado al endpoint
    return report.to_dict()