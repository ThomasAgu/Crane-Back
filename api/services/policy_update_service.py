# policy_update_service.py

from os import path
from zipfile import Path
from api.clients.opa_client import update_policies_file
from pathlib import Path

from api.config.constants import OPA_RBAC_CONFIG_NAME
from api.services.rbac_policy_service import build_dynamic_rego, write_rego_file

def update_opa_policies_from_db(db):
    """
    1. Build dynamic Rego from DB
    2. Generate temp file
    3. Update OPA policies
    """
    rego = build_dynamic_rego(db)
    path = write_rego_file(rego)
    print("Archivo generado:", path)

        
    # Usa tu método actual
    return update_policies_file(OPA_RBAC_CONFIG_NAME, path, force=True)
