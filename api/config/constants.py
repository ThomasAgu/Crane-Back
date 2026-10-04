import os
from dotenv import load_dotenv


load_dotenv()

# API
API_PREFIX = "/api"

# Secret key for JWT authentication
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SECRET = os.getenv("JWT_SECRET") or "secret"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"
JWT_EXPIRATION_TIME_MINUTES = int(
    os.getenv("JWT_EXPIRATION_TIME_MINUTES") or 15)

# Sqlite database file path
SQLITE_FILE = "sqlite:///./sql_app.db"

# Prometheus and Alert Manager constants
GLOBAL_SCRAPE_INTERVAL = "15s"
GLOBAL_EVALUATION_INTERVAL = "15s"
EXTERNAL_LABELS_MONITOR = "crane-monitor"
RULES_FILE = "rules.yml"
ALERT_MANAGER_SCHEME = "http"
ALERT_MANAGER_PORT = "9093"
PROMETHEUS_PORT = "9090"
PROMETHEUS_SCRAPE_JOB_NAME = "prometheus"
PROMETHEUS_SCRAPE_TIMEOUT = "10s"
PROMETHEUS_SCRAPE_INTERVAL = "5s"
PROMETHEUS_FILE = "prometheus.yml"
PROMETHEUS_NETWORK_NAME = "prometheus-net"
PROMETHEUS_NETWORK_DRIVER = "bridge"
MONITORING_SERVICE_NAME = "monitoring"
TARGET_PORT = "8080"

# OPA constants
OPA_RBAC_CONFIG_NAME = "rbac"
OPA_RBAC_CONFIG_FILE = "api/files/rules/policy/rbac.rego"
OPA_ALERT_RULES_CONFIG_NAME = "alert_rules"
OPA_ALERT_RULES_CONFIG_FILE = "api/files/rules/policy/alert.json"
OPA_SERVER_URL = "http://localhost:8181"
OPA_RBAC_RULE_NAME = "allow"
RULES_SERVICE_NAME = "rules"


# Docker compose constants
TEMP_FILES_PATH = "api/files/temp"
MONITORING_FILES_PATH = "api/files/monitoring"
RULES_FILES_PATH = "api/files/rules"
REMOVE_TEMP_FILES = False

# ANTES DE PUSHEAR METER COMO VARIABLES DE ENTORNO
GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID")
