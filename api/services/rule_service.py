''' Service to manage Open Policy Agent service '''
from fastapi import HTTPException
from api.clients.docker_client import get_docker_client
from api.config.constants import RULES_SERVICE_NAME


async def start_rules():
    ''' Start Open Policy Agent service '''
    try:
        docker = await get_docker_client(RULES_SERVICE_NAME)
        docker.compose.up(detach=True)
        return {"message": "Rules started successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting rules. {e}") from e


async def stop_rules():
    ''' Stop Open Policy Agent service '''
    try:
        docker = await get_docker_client(RULES_SERVICE_NAME)
        docker.compose.stop()
        return {"message": "Rules stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error stopping rules. Please check if the rules service is running") from e


async def restart_rules():
    ''' Restart Open Policy Agent service '''
    try:
        docker = await get_docker_client(RULES_SERVICE_NAME)
        docker.compose.restart()
        return {"message": "Rules restarted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error restarting rules. Please check if the rules service is running") from e
