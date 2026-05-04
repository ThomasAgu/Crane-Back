"""
stress_engine.py
----------------
Motor de Stress Testing. Ejecuta escenarios de carga sobre un servicio HTTP
usando Locust en modo programático (headless), sin levantar la web UI.

Cada método público corresponde a un `function_name` de la categoría "stress"
en la base de datos de escenarios.

Dependencias:
    pip install locust
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from locust import HttpUser, task, between, constant
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging

logger = logging.getLogger(__name__)
setup_logging("WARNING", None)



@dataclass
class StressResult:
    scenario_name: str
    target_host: str
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    events: list[dict] = field(default_factory=list)

    # Métricas agregadas que se llenan al finalizar
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    error_rate_pct: float = 0.0
    per_endpoint_stats: list[dict] = field(default_factory=list)

    def add_event(self, message: str):
        self.events.append({"ts": time.time(), "msg": message})
        logger.info("[StressEngine] %s", message)

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
# Usuarios Locust genéricos (se parametrizan dinámicamente)
# ---------------------------------------------------------------------------

class _GenericGetUser(HttpUser):
    """Usuario que hace GET / a intervalos regulares."""
    wait_time = between(0.5, 1.5)
    abstract = True

    @task
    def index(self):
        self.client.get("/")


class _HeavyPayloadUser(HttpUser):
    """Usuario que envía POSTs con payloads grandes."""
    wait_time = between(1, 2)
    abstract = True
    payload_size_kb: int = 512

    @task
    def post_large(self):
        data = "x" * (self.payload_size_kb * 1024)
        self.client.post("/", data=data, headers={"Content-Type": "text/plain"})


class _CpuBoundUser(HttpUser):
    """Usuario orientado a endpoints CPU-intensivos."""
    wait_time = constant(0.1)
    abstract = True
    cpu_endpoint: str = "/cpu"

    @task
    def cpu_task(self):
        self.client.get(self.cpu_endpoint)


class _IoBoundUser(HttpUser):
    """Usuario orientado a endpoints I/O-intensivos."""
    wait_time = constant(0.2)
    abstract = True
    io_endpoint: str = "/io"

    @task
    def io_task(self):
        self.client.get(self.io_endpoint)


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------

class StressEngine:
    """
    Ejecuta escenarios de stress testing sobre un servicio HTTP usando Locust.

    Uso:
        engine = StressEngine(host="http://localhost:8080")
        result  = await engine.run("spike", duration=60)
    """

    DEFAULT_DURATION = 60
    DEFAULT_USERS = 10

    def __init__(self, host: str):
        # Asegurar que el host tenga esquema
        if not host.startswith("http"):
            host = f"http://{host}"
        self.host = host

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    async def run(
        self,
        function_name: str,
        duration: int = DEFAULT_DURATION,
        **kwargs,
    ) -> StressResult:
        """
        Punto de entrada. Recibe el `function_name` del escenario y lo ejecuta.

        Args:
            function_name: nombre de la función del escenario (ej. "spike").
            duration:       duración total en segundos.
            **kwargs:       parámetros adicionales (users, spawn_rate, etc.).

        Returns:
            StressResult con métricas y eventos.
        """
        result = StressResult(scenario_name=function_name, target_host=self.host)

        handler = getattr(self, function_name, None)
        if handler is None:
            result.finish(success=False, error=f"Función '{function_name}' no encontrada en StressEngine.")
            return result

        try:
            result.add_event(f"Iniciando escenario '{function_name}' contra {self.host} por {duration}s")
            await handler(result, duration=duration, **kwargs)
            result.finish(success=True)
            result.add_event("Escenario de stress finalizado.")
        except Exception as exc:
            result.finish(success=False, error=str(exc))
            result.add_event(f"Error durante el escenario: {exc}")
            logger.exception("[StressEngine] Error en '%s'", function_name)

        return result

    # ------------------------------------------------------------------
    # Escenarios de stress
    # ------------------------------------------------------------------

    async def linear_load(
        self,
        result: StressResult,
        duration: int = DEFAULT_DURATION,
        max_users: int = 50,
        spawn_rate: float = 1.0,
        **_,
    ):
        """Linear Load Increase — incrementa usuarios progresivamente."""
        result.add_event(f"Carga lineal: 0 → {max_users} usuarios a {spawn_rate}/s")
        await self._run_locust(
            result,
            user_class=_GenericGetUser,
            users=max_users,
            spawn_rate=spawn_rate,
            duration=duration,
        )

    async def spike(
        self,
        result: StressResult,
        duration: int = DEFAULT_DURATION,
        peak_users: int = 200,
        spawn_rate: float = 50.0,
        **_,
    ):
        """Traffic Spike — pico repentino de tráfico."""
        result.add_event(f"Spike: {peak_users} usuarios a {spawn_rate}/s por {duration}s")
        await self._run_locust(
            result,
            user_class=_GenericGetUser,
            users=peak_users,
            spawn_rate=spawn_rate,
            duration=duration,
        )

    async def soak(
        self,
        result: StressResult,
        duration: int = 300,
        users: int = 20,
        **_,
    ):
        """Soak Test — carga sostenida durante un periodo prolongado."""
        result.add_event(f"Soak test: {users} usuarios sostenidos por {duration}s")
        await self._run_locust(
            result,
            user_class=_GenericGetUser,
            users=users,
            spawn_rate=users,  # todos a la vez
            duration=duration,
        )

    async def cpu_bound(
        self,
        result: StressResult,
        duration: int = DEFAULT_DURATION,
        users: int = 30,
        endpoint: str = "/cpu",
        **_,
    ):
        """CPU-bound Traffic — solicitudes CPU-intensivas."""

        class _User(_CpuBoundUser):
            cpu_endpoint = endpoint
            abstract = False

        result.add_event(f"CPU-bound: {users} usuarios → {endpoint}")
        await self._run_locust(result, user_class=_User, users=users, spawn_rate=users, duration=duration)

    async def io_bound(
        self,
        result: StressResult,
        duration: int = DEFAULT_DURATION,
        users: int = 30,
        endpoint: str = "/io",
        **_,
    ):
        """IO-bound Traffic — solicitudes I/O-intensivas."""

        class _User(_IoBoundUser):
            io_endpoint = endpoint
            abstract = False

        result.add_event(f"IO-bound: {users} usuarios → {endpoint}")
        await self._run_locust(result, user_class=_User, users=users, spawn_rate=users, duration=duration)

    async def large_payload(
        self,
        result: StressResult,
        duration: int = DEFAULT_DURATION,
        users: int = 10,
        payload_kb: int = 512,
        **_,
    ):
        """Large Payload Requests — payloads grandes para estresar la red."""

        class _User(_HeavyPayloadUser):
            payload_size_kb = payload_kb
            abstract = False

        result.add_event(f"Large payload: {users} usuarios, {payload_kb}KB por request")
        await self._run_locust(result, user_class=_User, users=users, spawn_rate=users, duration=duration)

    async def spike_plateau(
        self,
        result: StressResult,
        duration: int = DEFAULT_DURATION,
        peak_users: int = 150,
        plateau_users: int = 50,
        **_,
    ):
        """Spike + Plateau — pico inicial seguido de carga estable."""
        spike_duration = min(30, duration // 3)
        plateau_duration = duration - spike_duration

        result.add_event(f"Spike: {peak_users} usuarios por {spike_duration}s")
        await self._run_locust(
            result, user_class=_GenericGetUser,
            users=peak_users, spawn_rate=50, duration=spike_duration,
        )

        result.add_event(f"Plateau: {plateau_users} usuarios por {plateau_duration}s")
        await self._run_locust(
            result, user_class=_GenericGetUser,
            users=plateau_users, spawn_rate=plateau_users, duration=plateau_duration,
            accumulate=True,
        )

    async def mixed(
        self,
        result: StressResult,
        duration: int = DEFAULT_DURATION,
        min_users: int = 10,
        max_users: int = 100,
        steps: int = 4,
        **_,
    ):
        """Mixed Stress Scenario — variaciones controladas de intensidad."""
        step_duration = duration // steps
        step_delta = (max_users - min_users) // steps

        for i in range(steps):
            users = min_users + (step_delta * i)
            result.add_event(f"Paso {i + 1}/{steps}: {users} usuarios por {step_duration}s")
            await self._run_locust(
                result, user_class=_GenericGetUser,
                users=users, spawn_rate=users, duration=step_duration,
                accumulate=True,
            )

    # ------------------------------------------------------------------
    # Runner de Locust (headless)
    # ------------------------------------------------------------------

    async def _run_locust(
        self,
        result: StressResult,
        user_class,
        users: int,
        spawn_rate: float,
        duration: int,
        accumulate: bool = False,
    ):
        """
        Ejecuta Locust en modo programático (sin web UI) en un thread pool
        para no bloquear el event loop de FastAPI.

        Args:
            accumulate: si True, suma las métricas a las existentes en lugar de reemplazarlas.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._locust_blocking,
            result,
            user_class,
            users,
            spawn_rate,
            duration,
            accumulate,
        )

    def _locust_blocking(
        self,
        result: StressResult,
        user_class,
        users: int,
        spawn_rate: float,
        duration: int,
        accumulate: bool,
    ):
        """Bloque síncrono que corre Locust. Se ejecuta en un thread separado."""
        # Forzar abstract = False para poder instanciarlo
        if getattr(user_class, "abstract", False):
            user_class = type(user_class.__name__, (user_class,), {"abstract": False, "host": self.host})
        else:
            user_class.host = self.host

        env = Environment(user_classes=[user_class], host=self.host)
        env.create_local_runner()

        env.runner.start(user_count=users, spawn_rate=spawn_rate)
        time.sleep(duration)
        env.runner.quit()

        # Recolectar métricas
        stats = env.runner.stats
        total = stats.total

        if not accumulate:
            result.total_requests = total.num_requests
            result.failed_requests = total.num_failures
            result.avg_response_time_ms = round(total.avg_response_time, 2)
            result.max_response_time_ms = round(total.max_response_time, 2)
            result.requests_per_second = round(total.current_rps, 2)
            result.p95_response_time_ms = round(total.get_response_time_percentile(0.95) or 0, 2)
            result.p99_response_time_ms = round(total.get_response_time_percentile(0.99) or 0, 2)
        else:
            result.total_requests += total.num_requests
            result.failed_requests += total.num_failures
            # Promediar tiempos de respuesta
            result.avg_response_time_ms = round(
                (result.avg_response_time_ms + total.avg_response_time) / 2, 2
            )
            result.max_response_time_ms = max(result.max_response_time_ms, total.max_response_time)
            result.requests_per_second = round(
                (result.requests_per_second + total.current_rps) / 2, 2
            )

        # Calcular tasa de error
        if result.total_requests > 0:
            result.error_rate_pct = round(
                (result.failed_requests / result.total_requests) * 100, 2
            )

        # Stats por endpoint
        for name, entry in stats.entries.items():
            result.per_endpoint_stats.append({
                "endpoint": name,
                "requests": entry.num_requests,
                "failures": entry.num_failures,
                "avg_ms": round(entry.avg_response_time, 2),
                "p95_ms": round(entry.get_response_time_percentile(0.95) or 0, 2),
            })