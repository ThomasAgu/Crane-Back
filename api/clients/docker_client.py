import logging
import platform
import subprocess
from glob import glob
from pathlib import Path
from python_on_whales import DockerClient, docker
from api.config.constants import TEMP_FILES_PATH, MONITORING_FILES_PATH, RULES_FILES_PATH


def verify_docker_daemon():
    ''' Verify if Docker daemon is running '''
    os_type = platform.system()

    if os_type == "Windows":
        # Windows: use `docker version` to check if Docker is running
        try:
            output = subprocess.check_output(
                ["docker", "version"], stderr=subprocess.STDOUT
            ).decode()
            if "Server:" in output:
                return True
        except subprocess.CalledProcessError:
            return False

    elif os_type == "Darwin":
        # MacOS: use `docker info` to check if Docker is running
        try:
            subprocess.check_output("docker info", shell=True)
            return True
        except subprocess.CalledProcessError:
            return False

    else:
        # Linux: use `docker info` to check if Docker is running
        try:
            subprocess.check_output("docker info", shell=True)
            return True
        except subprocess.CalledProcessError:
            return False

    return False


def docker_running():
    ''' Check if Docker is running '''
    logger = logging.getLogger("api-log")

    if not verify_docker_daemon():
        logger.error("Detectamos que Docker no está corriendo en este sistema")
        logger.error(
            "Por favor, inicie el servicio de Docker para que Crane funcione correctamente."
        )
        return False
    return True


async def get_docker_client(project_name):
    ''' Get Docker client '''

    paths = {
        'monitoring': MONITORING_FILES_PATH,
        'rules': RULES_FILES_PATH,
        'default': f'{TEMP_FILES_PATH}/{project_name}'
    }

    if project_name == 'GLOBAL':
        return docker

    path = paths.get(project_name, paths['default'])
    client = DockerClient(compose_files=glob(f'{Path.cwd()}/{path}/*.yml'))

    return client
