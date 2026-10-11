# rbac_policy_service.py

import logging
from sqlalchemy.orm import Session
from api.db.crud.role_crud import get_all as get_all_roles
from api.db.crud.permission_crud import get_all as get_all_permissions
from api.db.crud.role_crud import get_permissions_for_role as get_permissions_by_role
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

import logging
import tempfile

def write_rego_file(rego_content: str):
    """
    Writes generated Rego to a temporary file outside OPA's policy directory.
    Returns the full path to the created file.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".rego", encoding="utf-8", delete=False
    ) as rego_file:
        rego_file.write(rego_content)
        file_path = rego_file.name

    logging.warning(f"[RBAC] Nuevo archivo .rego generado en: {file_path}")
    return file_path


import re
import json

def parse_role_permissions_from_rego(rego_path: str):
    """
    Extracts the role_permissions dictionary from a .rego file and returns it as a Python dict.
    """
    with open(rego_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to extract the JSON-like block inside role_permissions := {...}
    match = re.search(r'role_permissions\s*:=\s*({.*?})\s*\n', content, re.DOTALL)
    if not match:
        raise ValueError("role_permissions block not found in Rego file")

    json_like = match.group(1)

    # Clean up the JSON-like structure to make it valid JSON
    json_like = re.sub(r",\s*}", "}", json_like)  # Remove trailing commas before closing braces
    json_like = re.sub(r",\s*]", "]", json_like)  # Remove trailing commas before closing brackets

    # Parse the cleaned JSON-like string
    try:
        return json.loads(json_like)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse role_permissions as JSON: {e}")
