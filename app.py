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
from api.config.constants import API_PREFIX, OPA_RBAC_CONFIG_NAME, OPA_RBAC_CONFIG_FILE, OPA_ALERT_RULES_CONFIG_NAME, OPA_ALERT_RULES_CONFIG_FILE
from api.clients.opa_client import update_policies_file, update_or_create_opa_data
from api.services.rule_service import start_rules
from api.services.monitoring_service import start_monitoring
from api.db.database import create_db_and_tables
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


@app.on_event("startup")
async def startup_event():
    ''' Start basic services on startup '''
    create_db_and_tables()
    await start_rules()
    await start_monitoring()
    update_policies_file(OPA_RBAC_CONFIG_NAME, OPA_RBAC_CONFIG_FILE, True)
    data = json.load(open(OPA_ALERT_RULES_CONFIG_FILE, encoding='utf-8'))
    update_or_create_opa_data(data, OPA_ALERT_RULES_CONFIG_NAME)

router = APIRouter()

router.include_router(authRouter, prefix="/v1/auth")
router.include_router(ruleRouter, prefix="/v1/rules")
router.include_router(monitoringRouter, prefix="/v1/monitoring")
router.include_router(appRouter, prefix="/v1/apps")
router.include_router(roleRouter, prefix="/v1/roles")
router.include_router(userRouter, prefix="/v1/users")
router.include_router(permissionRouter, prefix="/v1/permissions")

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