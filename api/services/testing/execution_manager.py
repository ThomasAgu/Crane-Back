
"""
execution_manager.py
--------------------
Orquestador central del sistema de testing de escenarios.

Es el único punto de entrada desde `scenario_service`. Se encarga de:
  1. Resolver el contenedor y la URL del servicio inspeccionando Docker en tiempo real.
  2. Determinar qué motor usar (chaos o stress) según la categoría del escenario.
  3. Iniciar el AlertCollector en background durante la ejecución.
  4. Invocar el motor correcto con los parámetros del escenario.
  5. Detener el AlertCollector y recolectar las alertas.
  6. Generar el reporte final con ReportGenerator.
  7. Devolver el reporte al servicio que lo llamó.

Dependencias internas:
    chaos_engine.py, stress_engine.py, alert_collector.py,
    report_generator.py, docker_resolver.py
"""

import logging
from typing import Optional

from .alert_collector import AlertCollector
from .chaos_engine import ChaosEngine
from .docker_resolver import DockerResolver, ResolvedContainer
from .report_generator import ReportGenerator, ScenarioReport
from .stress_engine import StressEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Clase auxiliar: contexto de la app bajo test
# ---------------------------------------------------------------------------

class AppContext:
    """
    Encapsula la información necesaria para ejecutar un escenario sobre una app.
    Usa DockerResolver para descubrir el contenedor y la URL del servicio
    dinámicamente — no depende de campos extras en el modelo App.

    Solo requiere que App tenga: id, name.
    """

    def __init__(self, app, resolved: ResolvedContainer):
        self.app_id: int = app.id
        self.app_name: str = app.name
        self.container_name: str = resolved.container_name
        self.service_url: str = resolved.service_url
        self.project_name: str = resolved.service_name  # conservado del resolver
        self._resolved = resolved

    @classmethod
    async def from_app(cls, app) -> "AppContext":
        """
        Factory que resuelve el contenedor en Docker y construye el contexto.
        Usa get_docker_client(project_name) igual que el resto del proyecto.
        Lanza HTTPException si el contenedor no está disponible.

        Requiere que App tenga: id, name, y acceso al project_name.
        Ajustar la línea de project_name según tu modelo real:
          - Si App.project_name existe directamente → getattr(app, "project_name")
          - Si App tiene FK a Project             → app.project.name
        """
        project_name = (
            getattr(app, "project_name", None)
            or getattr(getattr(app, "project", None), "name", None)
            or app.name  # último fallback
        )

        resolver = DockerResolver()
        resolved = await resolver.resolve(app_name=app.name, project_name=project_name)
        return cls(app, resolved)

    def validate(self):
        """Validación post-construcción (DockerResolver ya garantiza los datos)."""
        if not self.container_name or not self.service_url:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail=f"No se pudo resolver el contenedor para la app '{self.app_name}'."
            )


# ---------------------------------------------------------------------------
# Clase auxiliar: parámetros del escenario
# ---------------------------------------------------------------------------

class ScenarioParams:
    """
    Convierte el modelo ORM de Scenario en parámetros tipados.

    Adaptar según los campos reales del modelo Scenario.
    """

    def __init__(self, scenario):
        self.scenario_id: int = scenario.id
        self.name: str = scenario.name
        self.category: str = scenario.category        # "chaos" | "stress"
        self.function_name: str = scenario.function_name
        self.duration: int = getattr(scenario, "duration", 30)

        # Parámetros opcionales JSON almacenados en el escenario (si los tenés)
        self.extra: dict = getattr(scenario, "extra_params", None) or {}

    def validate(self):
        if self.category not in ("chaos", "stress"):
            raise HTTPException(
                status_code=422,
                detail=f"Categoría de escenario inválida: '{self.category}'. "
                       f"Debe ser 'chaos' o 'stress'."
            )
        if not self.function_name:
            raise HTTPException(
                status_code=422,
                detail="El escenario no tiene 'function_name' definido."
            )


# ---------------------------------------------------------------------------
# ExecutionManager
# ---------------------------------------------------------------------------

class ExecutionManager:
    """
    Orquestador principal del motor de testing.

    Uso desde scenario_service:
        manager = ExecutionManager()
        report  = await manager.execute(db_scenario, db_app)
        return report.to_dict()
    """

    def __init__(
        self,
        alertmanager_url: str = "http://alertmanager:9093/api/v2/alerts",
        alert_poll_interval: int = 5,
        report_generator: Optional[ReportGenerator] = None,
    ):
        self.alertmanager_url = alertmanager_url
        self.alert_poll_interval = alert_poll_interval
        self.report_generator = report_generator or ReportGenerator()

    async def execute(self, scenario, app) -> ScenarioReport:
        """
        Ejecuta el escenario completo y devuelve el reporte.

        Args:
            scenario: modelo ORM del escenario (con id, name, category, function_name, etc.)
            app:      modelo ORM de la app (con id, name, container_name, host, port, etc.)

        Returns:
            ScenarioReport con todos los resultados, métricas y alertas.
        """
        # 1. Construir y validar contexto
        # AppContext.from_app() llama a DockerResolver — puede lanzar 404/422
        scenario_params = ScenarioParams(scenario)
        app_context = await AppContext.from_app(app)  # async: llama a get_docker_client()

        scenario_params.validate()
        app_context.validate()

        logger.info(
            "[ExecutionManager] Ejecutando escenario '%s' [%s] en app '%s'",
            scenario_params.name, scenario_params.category, app_context.app_name
        )

        # 2. Iniciar AlertCollector en background
        collector = AlertCollector(
            app_name=app_context.app_name,
            alertmanager_url=self.alertmanager_url,
            poll_interval=self.alert_poll_interval,
        )
        await collector.start()

        # 3. Ejecutar el motor correspondiente
        engine_result = None
        try:
            if scenario_params.category == "chaos":
                engine_result = await self._run_chaos(scenario_params, app_context)
            else:
                engine_result = await self._run_stress(scenario_params, app_context)
        finally:
            # 4. Detener AlertCollector pase lo que pase
            await collector.stop()

        # 5. Construir el reporte
        alert_events = collector.get_events()
        alert_summary = collector.get_summary()

        report = self.report_generator.build(
            scenario_id=scenario_params.scenario_id,
            scenario_name=scenario_params.name,
            scenario_category=scenario_params.category,
            app_id=app_context.app_id,
            app_name=app_context.app_name,
            app_host=app_context.service_url,
            engine_result=engine_result,
            alert_events=alert_events,
            alert_summary=alert_summary,
        )

        logger.info(
            "[ExecutionManager] Reporte generado. Veredicto: %s", report.verdict
        )

        # Log del reporte formateado (útil para debug)
        logger.debug("\n%s", report.to_string())

        return report

    # ------------------------------------------------------------------
    # Runners internos
    # ------------------------------------------------------------------

    async def _run_chaos(self, params: ScenarioParams, ctx: AppContext):
        """Instancia el ChaosEngine y ejecuta el escenario."""
        engine = ChaosEngine(
            container_name=ctx.container_name,
            project_name=ctx.project_name,
        )
        return await engine.run(
            function_name=params.function_name,
            duration=params.duration,
            **params.extra,
        )

    async def _run_stress(self, params: ScenarioParams, ctx: AppContext):
        """Instancia el StressEngine y ejecuta el escenario."""
        engine = StressEngine(host=ctx.service_url)
        return await engine.run(
            function_name=params.function_name,
            duration=params.duration,
            **params.extra,
        )