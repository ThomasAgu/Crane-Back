''' This module contains the routes for the rule service '''
from fastapi import APIRouter, Depends
import api.services.rule_service as RuleService
from api.routes.auth_routes import verify_jwt

ruleRouter = APIRouter()


@ruleRouter.post("/", tags=["Rules"], description="Start Open Policy Agent service", response_model_exclude_none=True, dependencies=[Depends(verify_jwt)])
async def start():
    apps = await RuleService.start_rules()
    return apps


@ruleRouter.post("/stop", tags=["Rules"], description="Stop Open Policy Agent service", response_model_exclude_none=True, dependencies=[Depends(verify_jwt)])
async def stop():
    apps = await RuleService.stop_rules()
    return apps


@ruleRouter.post("/restart", tags=["Rules"], description="Restart Open Policy Agent service", response_model_exclude_none=True, dependencies=[Depends(verify_jwt)])
async def restart():
    apps = await RuleService.restart_rules()
    return apps
