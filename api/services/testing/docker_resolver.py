"""
docker_resolver.py
------------------
Resuelve dinámicamente el nombre del contenedor y la URL accesible de un servicio
a partir del nombre de la app (App.name) y su project_name (nombre del proyecto Compose).

Usa python-on-whales (la misma librería que el resto del proyecto) para mantener
consistencia. El cliente Compose se obtiene con get_docker_client(), igual que
en el resto de la aplicación.

Dependencias:
    python-on-whales (ya instalada en el proyecto)
"""

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException
from python_on_whales import DockerClient

from api.clients.docker_client import get_docker_client

logger = logging.getLogger(__name__)

# Puertos HTTP comunes, en orden de preferencia
_PREFERRED_PORTS = [80, 8080, 3000, 5000, 8000, 4000]


@dataclass
class ResolvedContainer:
    """Resultado de la resolución de un contenedor."""
    container_id: str
    container_name: str       # nombre real del contenedor en Docker
    service_name: str         # nombre lógico del servicio (app.name)
    service_url: str          # URL HTTP accesible para el stress engine
    internal_ip: Optional[str]
    host_port: Optional[int]
    network_name: Optional[str]


class DockerResolver:
    """
    Resuelve el contenedor y la URL HTTP de un servicio Compose a partir
    del nombre de la app y su project_name, usando python-on-whales.

    Uso:
        resolver = DockerResolver()
        resolved = await resolver.resolve(app_name="api", project_name="mi_proyecto")
        # resolved.container_name → "mi_proyecto-api-1"
        # resolved.service_url    → "http://172.18.0.4:8080"
    """

    async def resolve(self, app_name: str, project_name: str) -> ResolvedContainer:
        """
        Localiza el contenedor del servicio y construye su URL accesible.

        Args:
            app_name:     App.name — nombre del servicio dentro del Compose.
            project_name: nombre del proyecto Compose (para obtener el cliente
                          con get_docker_client(), igual que en el resto del proyecto).

        Returns:
            ResolvedContainer listo para usar en ChaosEngine y StressEngine.

        Raises:
            HTTPException 404 si el servicio no tiene contenedores activos.
            HTTPException 422 si no se puede determinar la URL del servicio.
        """
        client: DockerClient = await get_docker_client(project_name)
        container = self._find_running_container(client, app_name, project_name)

        internal_ip, network_name = self._get_internal_ip(container)
        host_port = self._get_host_port(container)
        port = self._pick_port(container)

        # Preferir IP interna de la red Compose (estable y sin necesidad de
        # exponer el puerto al host). Fallback a puerto mapeado al host.
        if internal_ip and port:
            service_url = f"http://{internal_ip}:{port}"
        elif host_port:
            service_url = f"http://localhost:{host_port}"
        elif internal_ip:
            service_url = f"http://{internal_ip}"
        else:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"No se pudo determinar la URL del servicio '{app_name}' "
                    f"en el proyecto '{project_name}'. "
                    f"Verificá que el contenedor tenga una red o un puerto expuesto."
                ),
            )

        resolved = ResolvedContainer(
            container_id=container.id,
            container_name=container.name,
            service_name=app_name,
            service_url=service_url,
            internal_ip=internal_ip,
            host_port=host_port,
            network_name=network_name,
        )

        logger.info(
            "[DockerResolver] '%s/%s' → contenedor='%s' url='%s'",
            project_name, app_name, container.name, service_url,
        )
        return resolved

    # ------------------------------------------------------------------
    # Búsqueda del contenedor
    # ------------------------------------------------------------------

    def _find_running_container(self, client: DockerClient, app_name: str, project_name: str):
        """
        Busca el contenedor en estado 'running' del servicio app_name.

        Estrategia (en orden):
          1. client.compose.ps(services=[app_name]) — directo por nombre de servicio Compose.
          2. Filtro por labels com.docker.compose.project + service (más tolerante).
          3. Fuzzy match por nombre de contenedor como último recurso.
        """
        # Intento 1: compose ps filtrando por nombre de servicio
        try:
            containers = client.compose.ps(services=[app_name])
            running = [c for c in containers if c.state.running]
            if running:
                return running[0]
        except Exception as exc:
            logger.debug("[DockerResolver] compose.ps falló para '%s': %s", app_name, exc)

        # Intento 2: todos los contenedores del proyecto filtrados por labels Compose
        try:
            all_containers = client.ps(
                filters={
                    "label": [
                        f"com.docker.compose.project={project_name}",
                        f"com.docker.compose.service={app_name}",
                    ],
                    "status": "running",
                }
            )
            if all_containers:
                return all_containers[0]
        except Exception as exc:
            logger.debug("[DockerResolver] ps con labels falló: %s", exc)

        # Intento 3: fuzzy match en todos los contenedores corriendo
        try:
            all_running = client.ps(filters={"status": "running"})
            name_lower = app_name.lower()
            matches = [c for c in all_running if name_lower in c.name.lower()]
            if matches:
                matches.sort(key=lambda c: len(c.name))
                logger.warning(
                    "[DockerResolver] Fuzzy match para '%s': usando contenedor '%s'",
                    app_name, matches[0].name,
                )
                return matches[0]
        except Exception as exc:
            logger.debug("[DockerResolver] ps general falló: %s", exc)

        raise HTTPException(
            status_code=404,
            detail=(
                f"No se encontró ningún contenedor activo para el servicio '{app_name}' "
                f"en el proyecto '{project_name}'. "
                f"Verificá que el stack esté levantado con docker compose up."
            ),
        )

    # ------------------------------------------------------------------
    # Resolución de red y puertos
    # ------------------------------------------------------------------

    def _get_internal_ip(self, container) -> tuple[Optional[str], Optional[str]]:
        """
        Extrae la IP interna del contenedor.
        python-on-whales la expone en container.network_settings.networks,
        un dict de {network_name: NetworkInspectResult}.
        Prefiere redes Compose definidas por el usuario sobre la 'bridge' default.
        """
        try:
            networks: dict = container.network_settings.networks or {}
        except AttributeError:
            return None, None

        # Preferir redes que no sean la bridge por defecto
        for net_name, net_info in networks.items():
            if net_name == "bridge":
                continue
            ip = getattr(net_info, "ip_address", None)
            if ip:
                return ip, net_name

        # Fallback: primera red con IP disponible
        for net_name, net_info in networks.items():
            ip = getattr(net_info, "ip_address", None)
            if ip:
                return ip, net_name

        return None, None

    def _get_host_port(self, container) -> Optional[int]:
        """
        Devuelve el primer puerto mapeado al host, si existe.
        Útil como fallback para entornos sin red Compose compartida.
        """
        try:
            ports: dict = container.network_settings.ports or {}
        except AttributeError:
            return None

        for bindings in ports.values():
            if bindings:
                for binding in (bindings if isinstance(bindings, list) else [bindings]):
                    try:
                        return int(binding.host_port)
                    except (AttributeError, ValueError, TypeError):
                        continue
        return None

    def _pick_port(self, container) -> Optional[int]:
        """
        Elige el puerto TCP más apropiado expuesto por el contenedor.
        Prioriza puertos conocidos (_PREFERRED_PORTS); si no, usa el primero TCP.
        """
        try:
            ports: dict = container.network_settings.ports or {}
        except AttributeError:
            return None

        exposed_ports: list[int] = []
        for port_proto in ports.keys():
            # python-on-whales usa strings "8080/tcp" o enteros
            try:
                if isinstance(port_proto, str) and "/tcp" in port_proto:
                    exposed_ports.append(int(port_proto.split("/")[0]))
                elif isinstance(port_proto, int):
                    exposed_ports.append(port_proto)
            except ValueError:
                pass

        if not exposed_ports:
            # Intentar ExposedPorts desde la config de la imagen como último recurso
            try:
                for port_proto in (container.config.exposed_ports or {}):
                    if "/tcp" in str(port_proto):
                        exposed_ports.append(int(str(port_proto).split("/")[0]))
            except (AttributeError, ValueError):
                pass

        if not exposed_ports:
            return None

        for preferred in _PREFERRED_PORTS:
            if preferred in exposed_ports:
                return preferred

        return exposed_ports[0]