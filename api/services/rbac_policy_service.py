# rbac_policy_service.py

import logging
from sqlalchemy.orm import Session
from api.db.crud.role_crud import get_all as get_all_roles
from api.db.crud.permission_crud import get_all as get_all_permissions
from api.db.crud.role_crud import get_permissions_for_role as get_permissions_by_role
import tempfile
import json

def build_dynamic_rego(db: Session):
    """
    Build a dynamic RBAC Rego policy from DB.
    """

    roles = get_all_roles(db)
    policy = {}

    for role in roles:
        permissions = get_permissions_by_role(db, role.id)

        policy[role.name] = [
            {"action": p.action,  "object": p.object}
            for p in permissions
        ]

    # Armar el bloque completo del Rego
    rego = 'package rbac.authz\n\nimport rego.v1\n\n'
    rego += "role_permissions := {\n"

    for role_name, perms in policy.items():
        rego += f'    "{role_name}": [\n'
        for p in perms:
            rego += f'        {json.dumps(p)},\n'
        rego += "    ],\n"

    rego += "}\n\n"

    rego += """# logic that implements RBAC.
default allow := false
allow if {
    # lookup the list of roles for the user
    roles := input.roles

    # for each role in that list
    r := roles[_]

    # lookup the permissions list for role r
    permissions := role_permissions[r]

    # for each permission
    p := permissions[_]

    # check if the permission granted to r matches the user's request
    p == {"action": input.action, "object": input.object}
}
"""

    return rego

import os
import logging
from datetime import datetime

def write_rego_file(rego_content: str):
    """
    Writes rego content to a fixed path instead of a temporary file.
    Returns the full path to the created file.
    """
    # Ruta destino fija
    base_dir = r"C:\Users\t-agu\OneDrive\Escritorio\tuki\crane-rest-api\api\files\rules\policy"
    
    # Crear directorio si no existe
    os.makedirs(base_dir, exist_ok=True)
    
    # Nombre de archivo único
    filename = f"policy_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.rego"
    file_path = os.path.join(base_dir, filename)

    # Escribir archivo
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(rego_content)

    logging.warning(f"[RBAC] Nuevo archivo .rego generado en: {file_path}")
    return file_path
