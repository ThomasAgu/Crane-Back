''' Main application file '''
import json
from logging.config import dictConfig
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from api.config.logger import LogConfig
from api.clients.docker_client import docker_running
from api.routes.auth_routes import authRouter
from api.routes.apps_routes import appRouter
from api.routes.role_routes import roleRouter
from api.routes.monitoring_routes import monitoringRouter
from api.routes.user_routes import userRouter
from api.routes.rule_routes import ruleRouter
from api.routes.permission_routes import permissionRouter
from api.routes.repository_routes import repositoryRouter
from api.routes.alert_routes import alertRouter
from api.routes.actions_routes import actionRouter
from api.config.constants import API_PREFIX, OPA_RBAC_CONFIG_NAME, OPA_RBAC_CONFIG_FILE, OPA_ALERT_RULES_CONFIG_NAME, OPA_ALERT_RULES_CONFIG_FILE
from api.clients.opa_client import update_policies_file, update_or_create_opa_data
from api.services.policy_update_service import update_or_create_roles_and_permissions_in_db
from api.services.rule_service import start_rules
from api.services.monitoring_service import start_monitoring
from api.db.database import create_db_and_tables
from api.db.crud import action_crud
from api.db.schemas import ActionCreate
from fastapi.middleware.cors import CORSMiddleware

dictConfig(LogConfig().dict())

# --- CORS configuration ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

load_dotenv()
app = FastAPI()

''' Check if docker is running '''
if not docker_running():
    exit(0)


def populate_firing_actions(db):
    ''' Populate firing_actions table from configuration file '''
    from api.db import models
    import os
    
    # Load actions from JSON configuration file
    config_file = os.path.join(os.path.dirname(__file__), 'api', 'files', 'firing_actions.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            actions_config = json.load(f)
        
        for action_config in actions_config:
            # Check if action already exists to avoid duplicates
            existing_action = db.query(models.Action).filter(
                models.Action.name == action_config['name']
            ).first()
            
            if not existing_action:
                # Create the action
                action_data = ActionCreate(
                    name=action_config['name'],
                    description=action_config['description']
                )
                action_crud.create(db, action_data)
                print(f"Created firing action: {action_config['name']}")
    except FileNotFoundError:
        print(f"Warning: Configuration file not found at {config_file}")


@app.on_event("startup")
async def startup_event():
    ''' Start basic services on startup '''
    from api.db.database import SessionLocal
    
    create_db_and_tables()
    await start_rules()
    await start_monitoring()
    update_policies_file(OPA_RBAC_CONFIG_NAME, OPA_RBAC_CONFIG_FILE, True)
    # se va a ir esto me parece porque ya lo tenemos en base de datos
    data = json.load(open(OPA_ALERT_RULES_CONFIG_FILE, encoding='utf-8'))
    update_or_create_opa_data(data, OPA_ALERT_RULES_CONFIG_NAME)
    update_or_create_roles_and_permissions_in_db()
    # Populate firing_actions in the database
    db = SessionLocal()
    try:
        populate_firing_actions(db)
    finally:
        db.close()

router = APIRouter()

router.include_router(authRouter, prefix="/v1/auth")
router.include_router(ruleRouter, prefix="/v1/rules")
router.include_router(monitoringRouter, prefix="/v1/monitoring")
router.include_router(appRouter, prefix="/v1/apps")
router.include_router(roleRouter, prefix="/v1/roles")
router.include_router(userRouter, prefix="/v1/users")
router.include_router(permissionRouter, prefix="/v1/permissions")
router.include_router(repositoryRouter, prefix="/v1/repository")
router.include_router(actionRouter, prefix="/v1/action")
router.include_router(alertRouter, prefix="/v1/alert")

app.include_router(router, prefix=API_PREFIX)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization"], 
)