"""
report_generator.py
-------------------
Genera reportes legibles a partir de los resultados de escenarios de stress y chaos,
incluyendo las alertas capturadas durante la ejecución.

El reporte se devuelve tanto como dict estructurado (para la API) como string
formateado (para logs o display).

No tiene dependencias externas.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from chaos_engine import ChaosResult
    from stress_engine import StressResult
    from alert_collector import AlertEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Modelo del reporte
# ---------------------------------------------------------------------------

@dataclass
class ScenarioReport:
    """Reporte completo de un escenario ejecutado."""

    # Metadata
    scenario_id: int
    scenario_name: str
    scenario_category: str        # "chaos" | "stress"
    app_id: int
    app_name: str
    app_host: str

    # Resultado crudo
    success: bool
    duration_seconds: float
    error: Optional[str]
    events: list[dict]

    # Métricas de stress (solo para categoría "stress")
    stress_metrics: Optional[dict] = None

    # Alertas capturadas durante el test
    alert_summary: Optional[dict] = None

    # Evaluación final
    verdict: str = "UNKNOWN"      # "PASSED" | "FAILED" | "DEGRADED"
    verdict_reasons: list[str] = field(default_factory=list)

    # Timestamp
    generated_at: str = field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z"
    )

    def to_dict(self) -> dict:
        return {
            "metadata": {
                "scenario_id": self.scenario_id,
                "scenario_name": self.scenario_name,
                "scenario_category": self.scenario_category,
                "app_id": self.app_id,
                "app_name": self.app_name,
                "app_host": self.app_host,
                "generated_at": self.generated_at,
            },
            "execution": {
                "success": self.success,
                "duration_seconds": self.duration_seconds,
                "error": self.error,
                "events": self.events,
            },
            "stress_metrics": self.stress_metrics,
            "alert_summary": self.alert_summary,
            "verdict": {
                "result": self.verdict,
                "reasons": self.verdict_reasons,
            },
        }

    def to_string(self) -> str:
        """Devuelve una representación legible del reporte."""
        lines = [
            "=" * 65,
            f"  REPORTE DE ESCENARIO: {self.scenario_name.upper()}",
            "=" * 65,
            f"  App        : {self.app_name} (ID: {self.app_id})",
            f"  Host       : {self.app_host}",
            f"  Categoría  : {self.scenario_category}",
            f"  Duración   : {self.duration_seconds}s",
            f"  Generado   : {self.generated_at}",
            "-" * 65,
        ]

        # Veredicto
        verdict_icon = {"PASSED": "✅", "FAILED": "❌", "DEGRADED": "⚠️"}.get(self.verdict, "❓")
        lines.append(f"  VEREDICTO  : {verdict_icon} {self.verdict}")
        for reason in self.verdict_reasons:
            lines.append(f"               → {reason}")
        lines.append("-" * 65)

        # Línea de tiempo de eventos
        lines.append("  EVENTOS DEL ESCENARIO:")
        for ev in self.events:
            ts = datetime.datetime.fromtimestamp(ev["ts"]).strftime("%H:%M:%S")
            lines.append(f"    [{ts}] {ev['msg']}")

        # Métricas de stress
        if self.stress_metrics:
            lines.append("-" * 65)
            lines.append("  MÉTRICAS DE CARGA:")
            m = self.stress_metrics
            lines.append(f"    Requests totales  : {m.get('total_requests', 0)}")
            lines.append(f"    Requests fallidos : {m.get('failed_requests', 0)}")
            lines.append(f"    Tasa de error     : {m.get('error_rate_pct', 0)}%")
            lines.append(f"    Req/s             : {m.get('requests_per_second', 0)}")
            lines.append(f"    Tiempo prom (ms)  : {m.get('avg_response_time_ms', 0)}")
            lines.append(f"    P95 (ms)          : {m.get('p95_response_time_ms', 0)}")
            lines.append(f"    P99 (ms)          : {m.get('p99_response_time_ms', 0)}")
            lines.append(f"    Máximo (ms)       : {m.get('max_response_time_ms', 0)}")

            per_ep = m.get("per_endpoint_stats", [])
            if per_ep:
                lines.append("    Por endpoint:")
                for ep in per_ep:
                    lines.append(
                        f"      {ep['endpoint']} "
                        f"req={ep['requests']} fail={ep['failures']} "
                        f"avg={ep['avg_ms']}ms p95={ep['p95_ms']}ms"
                    )

        # Alertas
        if self.alert_summary:
            lines.append("-" * 65)
            lines.append("  ALERTAS DETECTADAS DURANTE EL TEST:")
            s = self.alert_summary
            lines.append(f"    Total capturadas : {s.get('total_captured', 0)}")
            lines.append(f"    En estado firing : {s.get('total_firing', 0)}")
            lines.append(f"    Resueltas        : {s.get('total_resolved', 0)}")

            for alert in s.get("alerts", []):
                icon = "🔴" if alert["status"] == "firing" else "🟢"
                lines.append(
                    f"    {icon} [{alert['status'].upper()}] "
                    f"{alert['name']} — severity: {alert['severity']}"
                )
                if alert.get("annotations", {}).get("summary"):
                    lines.append(f"         {alert['annotations']['summary']}")

        # Error si hubo
        if self.error:
            lines.append("-" * 65)
            lines.append(f"  ERROR: {self.error}")

        lines.append("=" * 65)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generador
# ---------------------------------------------------------------------------

class ReportGenerator:
    """
    Construye un ScenarioReport a partir de los resultados del motor
    (ChaosResult o StressResult) y las alertas recolectadas.

    Umbrales de calidad configurables por instancia.
    """

    def __init__(
        self,
        error_rate_threshold_pct: float = 5.0,
        p95_threshold_ms: float = 2000.0,
        max_response_threshold_ms: float = 10000.0,
        critical_alert_severities: list[str] = None,
    ):
        self.error_rate_threshold_pct = error_rate_threshold_pct
        self.p95_threshold_ms = p95_threshold_ms
        self.max_response_threshold_ms = max_response_threshold_ms
        self.critical_alert_severities = critical_alert_severities or ["critical", "page"]

    def build(
        self,
        scenario_id: int,
        scenario_name: str,
        scenario_category: str,
        app_id: int,
        app_name: str,
        app_host: str,
        engine_result: Union["ChaosResult", "StressResult"],
        alert_events: list["AlertEvent"] = None,
        alert_summary: Optional[dict] = None,
    ) -> ScenarioReport:
        """
        Construye el reporte completo.

        Args:
            engine_result:  ChaosResult o StressResult del motor correspondiente.
            alert_events:   lista de AlertEvent capturados (opcional).
            alert_summary:  dict de resumen de AlertCollector (opcional).
        """
        # Métricas de stress (solo aplica para StressResult)
        stress_metrics = self._extract_stress_metrics(engine_result, scenario_category)

        report = ScenarioReport(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            scenario_category=scenario_category,
            app_id=app_id,
            app_name=app_name,
            app_host=app_host,
            success=engine_result.success,
            duration_seconds=engine_result.duration_seconds,
            error=engine_result.error,
            events=engine_result.events,
            stress_metrics=stress_metrics,
            alert_summary=alert_summary,
        )

        # Evaluar veredicto
        report.verdict, report.verdict_reasons = self._evaluate_verdict(
            report, alert_events or []
        )

        logger.info(
            "[ReportGenerator] Reporte generado para escenario '%s': %s",
            scenario_name, report.verdict
        )
        return report

    # ------------------------------------------------------------------
    # Extracción de métricas
    # ------------------------------------------------------------------

    def _extract_stress_metrics(self, result, category: str) -> Optional[dict]:
        """Extrae las métricas de stress si el resultado es un StressResult."""
        if category != "stress":
            return None

        return {
            "total_requests": getattr(result, "total_requests", 0),
            "failed_requests": getattr(result, "failed_requests", 0),
            "avg_response_time_ms": getattr(result, "avg_response_time_ms", 0.0),
            "p95_response_time_ms": getattr(result, "p95_response_time_ms", 0.0),
            "p99_response_time_ms": getattr(result, "p99_response_time_ms", 0.0),
            "max_response_time_ms": getattr(result, "max_response_time_ms", 0.0),
            "requests_per_second": getattr(result, "requests_per_second", 0.0),
            "error_rate_pct": getattr(result, "error_rate_pct", 0.0),
            "per_endpoint_stats": getattr(result, "per_endpoint_stats", []),
        }

    # ------------------------------------------------------------------
    # Evaluación de veredicto
    # ------------------------------------------------------------------

    def _evaluate_verdict(
        self,
        report: ScenarioReport,
        alert_events: list["AlertEvent"],
    ) -> tuple[str, list[str]]:
        """
        Evalúa si el sistema pasó, degradó o falló el escenario.

        Reglas:
        - FAILED: el motor tuvo un error, o hay alertas críticas sin resolver.
        - DEGRADED: métricas por encima de umbrales, o alertas de baja severidad.
        - PASSED: todo dentro de los umbrales normales.
        """
        reasons: list[str] = []
        is_failed = False
        is_degraded = False

        # 1. Error del motor
        if not report.success or report.error:
            is_failed = True
            reasons.append(f"El escenario terminó con error: {report.error}")

        # 2. Métricas de stress
        if report.stress_metrics:
            m = report.stress_metrics
            if m["error_rate_pct"] > self.error_rate_threshold_pct:
                is_failed = True
                reasons.append(
                    f"Tasa de error {m['error_rate_pct']}% supera el umbral "
                    f"de {self.error_rate_threshold_pct}%"
                )
            if m["p95_response_time_ms"] > self.p95_threshold_ms:
                is_degraded = True
                reasons.append(
                    f"P95 de {m['p95_response_time_ms']}ms supera el umbral "
                    f"de {self.p95_threshold_ms}ms"
                )
            if m["max_response_time_ms"] > self.max_response_threshold_ms:
                is_degraded = True
                reasons.append(
                    f"Tiempo máximo de respuesta {m['max_response_time_ms']}ms "
                    f"supera el umbral de {self.max_response_threshold_ms}ms"
                )

        # 3. Alertas
        for alert in alert_events:
            if alert.status == "firing":
                if alert.severity in self.critical_alert_severities:
                    is_failed = True
                    reasons.append(
                        f"Alerta crítica disparada: {alert.name} "
                        f"(severity={alert.severity})"
                    )
                else:
                    is_degraded = True
                    reasons.append(
                        f"Alerta disparada: {alert.name} "
                        f"(severity={alert.severity})"
                    )

        # Determinar veredicto final
        if is_failed:
            verdict = "FAILED"
        elif is_degraded:
            verdict = "DEGRADED"
        else:
            verdict = "PASSED"
            reasons.append("Todas las métricas dentro de los umbrales esperados.")

        return verdict, reasons