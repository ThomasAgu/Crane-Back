"""
alert_collector.py
------------------
Recolector de alertas de Prometheus/AlertManager durante la ejecución de un escenario.

Hace polling a la API de AlertManager para capturar qué alertas se dispararon
y cuáles se resolvieron mientras el test estaba corriendo. Esta información
se integra al reporte final para validar que el sistema de alertas responde
correctamente al escenario ejecutado.

Dependencias:
    pip install httpx
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# URL de la API de AlertManager (configurable por env o settings)
ALERTMANAGER_API_URL = "http://localhost:9093/api/v2/alerts"


@dataclass
class AlertEvent:
    """Representa una alerta capturada durante el test."""
    name: str
    status: str          
    severity: str
    labels: dict
    annotations: dict
    starts_at: str
    ends_at: Optional[str]
    captured_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "severity": self.severity,
            "labels": self.labels,
            "annotations": self.annotations,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "captured_at": self.captured_at,
        }


class AlertCollector:
    """
    Recolecta alertas de AlertManager mientras un escenario está en ejecución.

    Uso típico (manejado internamente por ExecutionManager):
        collector = AlertCollector(app_name="mi_servicio", poll_interval=5)
        await collector.start()
        # ... ejecutar el escenario ...
        await collector.stop()
        alerts = collector.get_events()
    """

    def __init__(
        self,
        app_name: str,
        alertmanager_url: str = ALERTMANAGER_API_URL,
        poll_interval: int = 5,
    ):
        self.app_name = app_name
        self.alertmanager_url = alertmanager_url
        self.poll_interval = poll_interval
        self._events: list[AlertEvent] = []
        self._seen_fingerprints: set[str] = set()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Inicia el polling en background."""
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("[AlertCollector] Iniciado para app '%s'", self.app_name)

    async def stop(self):
        """Detiene el polling y espera a que el task finalice."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[AlertCollector] Detenido. Alertas capturadas: %d", len(self._events))

    def get_events(self) -> list[AlertEvent]:
        """Devuelve todas las alertas capturadas durante el test."""
        return list(self._events)

    def get_summary(self) -> dict:
        """Resumen de alertas para incluir en el reporte."""
        firing = [e for e in self._events if e.status == "firing"]
        resolved = [e for e in self._events if e.status == "resolved"]

        return {
            "total_captured": len(self._events),
            "total_firing": len(firing),
            "total_resolved": len(resolved),
            "alerts": [e.to_dict() for e in self._events],
            "unique_alert_names": list({e.name for e in self._events}),
        }

    # ------------------------------------------------------------------
    # Loop de polling
    # ------------------------------------------------------------------

    async def _poll_loop(self):
        async with httpx.AsyncClient(timeout=10) as client:
            while self._running:
                try:
                    await self._fetch_alerts(client)
                except httpx.RequestError as exc:
                    logger.warning("[AlertCollector] No se pudo conectar a AlertManager: %s", exc)
                except Exception as exc:
                    logger.error("[AlertCollector] Error inesperado: %s", exc)

                await asyncio.sleep(self.poll_interval)

    async def _fetch_alerts(self, client: httpx.AsyncClient):
        """Hace un GET a la API de AlertManager y procesa las alertas relevantes."""
        response = await client.get(
            self.alertmanager_url,
            params={"filter": f'job="{self.app_name}"'},
        )
        response.raise_for_status()
        alerts_data = response.json()

        for alert in alerts_data:
            fingerprint = alert.get("fingerprint", "")
            status = alert.get("status", {}).get("state", "unknown")
            labels = alert.get("labels", {})
            alert_name = labels.get("alertname", "unknown")

            # Evitar duplicados exactos (misma alerta en el mismo estado)
            key = f"{fingerprint}:{status}"
            if key in self._seen_fingerprints:
                continue
            self._seen_fingerprints.add(key)

            # Filtrar alertas relevantes para esta app
            if not self._is_relevant(labels):
                continue

            event = AlertEvent(
                name=alert_name,
                status=status,
                severity=labels.get("severity", "unknown"),
                labels=labels,
                annotations=alert.get("annotations", {}),
                starts_at=alert.get("startsAt", ""),
                ends_at=alert.get("endsAt"),
            )
            self._events.append(event)
            logger.info(
                "[AlertCollector] Nueva alerta: %s [%s] severity=%s",
                alert_name, status, event.severity
            )

    def _is_relevant(self, labels: dict) -> bool:
        """
        Determina si una alerta es relevante para la app bajo test.
        Acepta alertas que mencionen el nombre de la app en sus labels.
        """
        app_name_lower = self.app_name.lower()
        for value in labels.values():
            if isinstance(value, str) and app_name_lower in value.lower():
                return True
        return True  # Si no hay filtro preciso, captura todo durante el test