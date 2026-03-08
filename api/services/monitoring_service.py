''' This module contains the services for starting, stopping and restarting the monitoring services. '''
from fastapi import HTTPException
from api.clients.docker_client import get_docker_client
from api.services.generator_service import prometheus_yaml_generator
from api.config.constants import MONITORING_SERVICE_NAME, PROMETHEUS_NETWORK_NAME, PROMETHEUS_NETWORK_DRIVER

async def start_monitoring():
    ''' Start Prometheus and Alert Manager services'''
    try:
        prometheus_yaml_generator()
        docker = await get_docker_client(MONITORING_SERVICE_NAME)
        networks = docker.network.list()
        search = [
            network for network in networks
            if network.name == PROMETHEUS_NETWORK_NAME
        ]
        if not search:
            docker.network.create(
                PROMETHEUS_NETWORK_NAME,
                driver=PROMETHEUS_NETWORK_DRIVER
            )
        docker.compose.up(detach=True)
        return {"message": "Monitoring started successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting monitoring. {e}") from e


async def stop_monitoring():
    ''' Stop Prometheus and Alert Manager services '''
    try:
        docker = await get_docker_client(MONITORING_SERVICE_NAME)
        docker.compose.stop()
        return {"message": "Monitoring stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error stopping monitoring. Please check if the monitoring service is running") from e


async def restart_monitoring():
    ''' Restart Prometheus and Alert Manager services '''
    try:
        docker = await get_docker_client(MONITORING_SERVICE_NAME)
        docker.compose.restart()
        return {"message": "Monitoring restarted successfully"}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Error restarting monitoring. Please check if the monitoring service is running.") from None
