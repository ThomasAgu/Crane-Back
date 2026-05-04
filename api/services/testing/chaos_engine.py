"""
chaos_engine.py
---------------
Motor de Chaos Engineering. Ejecuta escenarios de caos sobre contenedores Docker
usando python-on-whales (la misma librería que el resto del proyecto),
comandos `tc` (traffic control) y `stress-ng`.

Cada método público corresponde a un `function_name` de la categoría "chaos"
en la base de datos de escenarios.

Dependencias:
    python-on-whales (ya instalada en el proyecto)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from python_on_whales import DockerClient, Container
from python_on_whales.exceptions import NoSuchContainer

from api.clients.docker_client import get_docker_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Resultado de un escenario de caos
# ---------------------------------------------------------------------------

@dataclass
class ChaosResult:
    scenario_name: str
    container_id: str
    container_name: str
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    events: list[dict] = field(default_factory=list)

    def add_event(self, message: str):
        self.events.append({"ts": time.time(), "msg": message})
        logger.info("[ChaosEngine] %s", message)

    def finish(self, success: bool, error: Optional[str] = None):
        self.finished_at = time.time()
        self.success = success
        self.error = error

    @property
    def duration_seconds(self) -> float:
        if self.finished_at:
            return round(self.finished_at - self.started_at, 2)
        return round(time.time() - self.started_at, 2)


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------

class ChaosEngine:
    """
    Ejecuta escenarios de chaos engineering sobre un contenedor Docker,
    usando python-on-whales igual que el resto del proyecto.

    Uso:
        engine = ChaosEngine(container_name="api", project_name="mi_proyecto")
        result = await engine.run("cpu_stress", duration=30)
    """

    DEFAULT_DURATION = 30

    def __init__(self, container_name: str, project_name: str):
        self.container_name = container_name
        self.project_name = project_name
        self._client: Optional[DockerClient] = None
        self._container: Optional[Container] = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    async def run(
        self,
        function_name: str,
        duration: int = DEFAULT_DURATION,
        **kwargs,
    ) -> ChaosResult:
        """
        Punto de entrada. Recibe el `function_name` del escenario y lo ejecuta.

        Args:
            function_name: nombre de la función del escenario (ej. "cpu_stress").
            duration:       duración en segundos del escenario.
            **kwargs:       parámetros adicionales específicos de cada escenario.

        Returns:
            ChaosResult con todos los eventos y el estado final.
        """
        client = await self._get_client()
        container = self._get_container(client)

        result = ChaosResult(
            scenario_name=function_name,
            container_id=container.id,
            container_name=container.name,
        )

        handler = getattr(self, function_name, None)
        if handler is None:
            result.finish(
                success=False,
                error=f"Función '{function_name}' no encontrada en ChaosEngine.",
            )
            return result

        try:
            result.add_event(
                f"Iniciando escenario '{function_name}' por {duration}s "
                f"en '{container.name}'"
            )
            await handler(client, container, result, duration=duration, **kwargs)
            result.finish(success=True)
            result.add_event("Escenario finalizado correctamente.")
        except Exception as exc:
            result.finish(success=False, error=str(exc))
            result.add_event(f"Error durante el escenario: {exc}")
            logger.exception("[ChaosEngine] Error inesperado en '%s'", function_name)

        return result

    # ------------------------------------------------------------------
    # Escenarios de Red
    # ------------------------------------------------------------------

    async def induce_latency(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        latency_ms: int = 200,
        **_,
    ):
        """Network Latency Spike — agrega latencia artificial con `tc netem`."""
        iface = "eth0"
        result.add_event(f"Agregando {latency_ms}ms de latencia en {iface}")
        self._exec(client, container, f"tc qdisc add dev {iface} root netem delay {latency_ms}ms")
        await asyncio.sleep(duration)
        result.add_event("Revirtiendo latencia de red")
        self._exec(client, container, f"tc qdisc del dev {iface} root")

    async def packet_loss(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        loss_pct: float = 10.0,
        **_,
    ):
        """Packet Loss Injection — introduce pérdida de paquetes con `tc netem`."""
        iface = "eth0"
        result.add_event(f"Activando {loss_pct}% de pérdida de paquetes en {iface}")
        self._exec(client, container, f"tc qdisc add dev {iface} root netem loss {loss_pct}%")
        await asyncio.sleep(duration)
        result.add_event("Revirtiendo pérdida de paquetes")
        self._exec(client, container, f"tc qdisc del dev {iface} root")

    async def bandwidth_limit(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        rate_kbps: int = 512,
        **_,
    ):
        """Bandwidth Throttling — limita el ancho de banda con `tc tbf`."""
        iface = "eth0"
        result.add_event(f"Limitando ancho de banda a {rate_kbps} kbps en {iface}")
        cmd = (
            f"tc qdisc add dev {iface} root tbf "
            f"rate {rate_kbps}kbit burst 32kbit latency 400ms"
        )
        self._exec(client, container, cmd)
        await asyncio.sleep(duration)
        result.add_event("Revirtiendo límite de ancho de banda")
        self._exec(client, container, f"tc qdisc del dev {iface} root")

    # ------------------------------------------------------------------
    # Escenarios de CPU / Memoria / Disco
    # ------------------------------------------------------------------

    async def cpu_stress(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        workers: int = 2,
        **_,
    ):
        """CPU Saturation — genera carga de CPU con `stress-ng`."""
        result.add_event(f"Iniciando stress de CPU con {workers} workers por {duration}s")
        # detach=True para no bloquear; el timeout de stress-ng lo detiene solo
        self._exec(
            client, container,
            f"stress-ng --cpu {workers} --timeout {duration}s",
            detach=True,
        )
        await asyncio.sleep(duration + 2)
        result.add_event("Stress de CPU finalizado")

    async def memory_stress(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        vm_bytes: str = "256M",
        **_,
    ):
        """Memory Pressure — simula presión de memoria con `stress-ng`."""
        result.add_event(f"Iniciando stress de memoria ({vm_bytes}) por {duration}s")
        self._exec(
            client, container,
            f"stress-ng --vm 1 --vm-bytes {vm_bytes} --timeout {duration}s",
            detach=True,
        )
        await asyncio.sleep(duration + 2)
        result.add_event("Stress de memoria finalizado")

    async def disk_io_limit(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        **_,
    ):
        """Disk I/O Throttling — restringe I/O de disco con `stress-ng --hdd`."""
        result.add_event(f"Iniciando stress de I/O de disco por {duration}s")
        self._exec(
            client, container,
            f"stress-ng --hdd 1 --timeout {duration}s",
            detach=True,
        )
        await asyncio.sleep(duration + 2)
        result.add_event("Stress de I/O finalizado")

    # ------------------------------------------------------------------
    # Escenarios de ciclo de vida del contenedor
    # ------------------------------------------------------------------

    async def kill_container(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        **_,
    ):
        """Kill Container — finaliza abruptamente el contenedor."""
        result.add_event(f"Terminando contenedor '{container.name}' con SIGKILL")
        client.kill(container, signal="SIGKILL")
        result.add_event("Contenedor terminado. Docker restart policy se encargará de reiniciarlo.")

        # Esperar a que Docker lo reinicie y reportar estado
        await asyncio.sleep(min(duration, 15))
        refreshed = self._inspect(client, container.id)
        status = refreshed.state.status if refreshed else "unknown"
        result.add_event(f"Estado del contenedor tras kill: {status}")

    async def restart_loop(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        restarts: int = 3,
        **_,
    ):
        """Restart Loop — reinicia el contenedor varias veces."""
        interval = max(duration // restarts, 5)
        for i in range(1, restarts + 1):
            result.add_event(f"Reinicio {i}/{restarts}")
            client.restart(container, time=3)
            refreshed = self._inspect(client, container.id)
            status = refreshed.state.status if refreshed else "unknown"
            result.add_event(f"Contenedor reiniciado. Estado: {status}")
            if i < restarts:
                await asyncio.sleep(interval)

    async def pause_container(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        **_,
    ):
        """Freeze Container — pausa la ejecución con `docker pause`."""
        result.add_event(f"Pausando contenedor '{container.name}' por {duration}s")
        client.pause(container)
        await asyncio.sleep(duration)
        result.add_event("Reanudando contenedor")
        client.unpause(container)
        refreshed = self._inspect(client, container.id)
        status = refreshed.state.status if refreshed else "unknown"
        result.add_event(f"Estado tras reanudar: {status}")

    async def dependency_latency(
        self,
        client: DockerClient,
        container: Container,
        result: ChaosResult,
        duration: int = DEFAULT_DURATION,
        dependency_name: Optional[str] = None,
        latency_ms: int = 500,
        **_,
    ):
        """
        Dependency Degradation — agrega latencia en un servicio del que depende el objetivo.
        Si no se especifica `dependency_name`, aplica la latencia en el mismo contenedor.
        """
        target_name = dependency_name or container.name
        result.add_event(f"Degradando dependencia '{target_name}' con {latency_ms}ms de latencia")

        # Resolver el contenedor dependencia dentro del mismo proyecto Compose
        dep_containers = client.ps(filters={"name": target_name, "status": "running"})
        if not dep_containers:
            raise RuntimeError(
                f"Contenedor dependencia '{target_name}' no encontrado o no está corriendo."
            )
        dep_container = dep_containers[0]

        self._exec(client, dep_container, f"tc qdisc add dev eth0 root netem delay {latency_ms}ms")
        result.add_event(f"Latencia aplicada en '{dep_container.name}'")
        await asyncio.sleep(duration)
        self._exec(client, dep_container, "tc qdisc del dev eth0 root")
        result.add_event(f"Latencia revertida en '{dep_container.name}'")

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _get_client(self) -> DockerClient:
        """Obtiene el cliente Compose usando get_docker_client(), igual que el resto del proyecto."""
        if self._client is None:
            self._client = await get_docker_client(self.project_name)
        return self._client

    def _get_container(self, client: DockerClient) -> Container:
        """
        Resuelve el contenedor por nombre real, no por servicio de Compose.
        Permite pasar nombres como 'prometheus', 'alertmanager',
        'prueba_demo_crane_2024-copy-2-whoami-1', etc.
        """

        if self._container is not None:
            return self._container

        # 1) Intentar encontrar el contenedor exacto
        try:
            self._container = client.container.get(self.container_name)
            return self._container
        except Exception:
            pass

        # 2) Buscar contenedores que contengan el nombre parcial
        matches = [
            c for c in client.container.list(all=True)
            if self.container_name in c.name
        ]

        if not matches:
            raise RuntimeError(
                f"No se encontró ningún contenedor que coincida con '{self.container_name}'."
            )

        # usar el primero por defecto
        self._container = matches[0]
        return self._container 

    @staticmethod
    def _exec(
        client: DockerClient,
        container: Container,
        cmd: str,
        detach: bool = False,
    ):
        """
        Ejecuta un comando dentro del contenedor usando client.execute().
        En python-on-whales la firma es: client.execute(container, command_list, detach=...).
        """
        command = cmd.split()
        logger.debug("[ChaosEngine] exec en %s: %s", container.name, cmd)
        try:
            result = client.execute(container, command, detach=detach)
            if not detach:
                logger.debug("[ChaosEngine] output: %s", result)
            return result
        except Exception as exc:
            logger.warning("[ChaosEngine] Comando falló en '%s': %s — %s", container.name, cmd, exc)
            raise

    @staticmethod
    def _inspect(client: DockerClient, container_id: str) -> Optional[Container]:
        """Re-inspecciona un contenedor para obtener su estado actualizado."""
        try:
            return client.container.inspect(container_id)
        except Exception:
            return None