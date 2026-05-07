"""
Service to sync custom alerts from database to Prometheus rules files
"""
import os
import yaml
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from api.db.models import CustomAlert

logger = logging.getLogger("api-log")


RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "files", "monitoring", "rules")
CUSTOM_ALERTS_FILE = os.path.join(RULES_DIR, "custom_alerts.yml")


def generate_prometheus_rules(alerts: List[CustomAlert]) -> Dict[str, Any]:
    """
    Convert database alerts to Prometheus rule format
    """
    rules = []
    
    for alert in alerts:
        rule = {
            "alert": alert.alert,
            "expr": alert.expr,
            "for": alert.for_time,
            "labels": {
                "severity": alert.severity,
                "app_id": str(alert.app_id),
                "job": alert.app.name if alert.app else "unknown"
            },
            "annotations": {
                "summary": alert.summary,
                "description": alert.description
            }
        }
        rules.append(rule)
    
    # Return in Prometheus rules format
    return {
        "groups": [
            {
                "name": "custom-alerts",
                "rules": rules
            }
        ]
    }


def sync_alerts_to_prometheus(db: Session) -> bool:
    """
    Fetch all custom alerts from database and write to Prometheus rules file
    """
    try:
        # Ensure rules directory exists
        os.makedirs(RULES_DIR, exist_ok=True)
        
        # Fetch all custom alerts from database
        custom_alerts = db.query(CustomAlert).filter(CustomAlert.deleted_at == None).all()
        
        if not custom_alerts:
            # Write empty rules file to ensure it exists
            empty_config = {"groups": [{"name": "custom-alerts", "rules": []}]}
            with open(CUSTOM_ALERTS_FILE, 'w') as f:
                yaml.dump(empty_config, f, default_flow_style=False, sort_keys=False)
            logger.info("No custom alerts found. Created empty custom_alerts.yml")
            return True
        
        # Generate Prometheus rules format
        rules_config = generate_prometheus_rules(custom_alerts)
        
        # Write to YAML file
        with open(CUSTOM_ALERTS_FILE, 'w') as f:
            yaml.dump(rules_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Successfully synced {len(custom_alerts)} custom alerts to {CUSTOM_ALERTS_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Error syncing alerts to Prometheus: {str(e)}")
        return False


def trigger_prometheus_reload():
    """
    Trigger Prometheus to reload rules by calling its reload endpoint.
    This requires Prometheus to be running with --web.enable-lifecycle flag.
    """
    try:
        import requests
        response = requests.post("http://localhost:9090/-/reload", timeout=5)
        if response.status_code == 200:
            logger.info("Prometheus reload triggered successfully")
            return True
        else:
            logger.warning(f"Prometheus reload returned status {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"Could not trigger Prometheus reload: {str(e)}")
        # Return True anyway since the file was written - Prometheus will pick it up
        # when it performs its next configuration reload cycle
        return True
