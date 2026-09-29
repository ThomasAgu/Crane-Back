package rbac.authz

import rego.v1

role_permissions := {
    "ADMIN": [
        {"action": "GET", "object": "USERS"},
        {"action": "POST", "object": "USERS"},
        {"action": "GET", "object": "ROLES"},
        {"action": "POST", "object": "ROLES"},
        {"action": "PATCH", "object": "ROLES"},
        {"action": "DELETE", "object": "ROLES"},
        {"action": "GET", "object": "PERMISSIONS"},
        {"action": "POST", "object": "PERMISSIONS"},
        {"action": "GET", "object": "REPOSITORYMODERATOR"},
        {"action": "GET", "object": "GROUPS"},
        {"action": "DELETE", "object": "GROUPS"},
        {"action": "POST", "object": "GROUPS"},
        {"action": "GET", "object": "TASKS"},
        {"action": "DELETE", "object": "TASKS"},
        {"action": "POST", "object": "TASKS"},
    ],
    "OPERATOR": [
        {"action": "GET", "object": "REPOSITORYMODERATOR"},
    ],
    "PROFESSOR": [
        {"action": "GET", "object": "GROUPS"},
        {"action": "GET", "object": "USERS"},
        {"action": "DELETE", "object": "GROUPS"},
        {"action": "POST", "object": "GROUPS"},
        {"action": "GET", "object": "TASKS"},
        {"action": "DELETE", "object": "TASKS"},
        {"action": "POST", "object": "TASKS"},
    ],
    "USER": [
        {"action": "GET", "object": "APPS"},
        {"action": "POST", "object": "APPS"},
        {"action": "PATCH", "object": "APPS"},
        {"action": "DELETE", "object": "APPS"},
        {"action": "GET", "object": "ROLES"},
        {"action": "GET", "object": "REPOSITORY"},
        {"action": "POST", "object": "REPOSITORY"},
        {"action": "PATCH", "object": "REPOSITORY"},
        {"action": "GET", "object": "OPA"},
        {"action": "POST", "object": "OPA"},
        {"action": "PATCH", "object": "OPA"},
        {"action": "DELETE", "object": "OPA"},
        {"action": "GET", "object": "MONITORING"},
        {"action": "POST", "object": "MONITORING"},
        {"action": "PATCH", "object": "MONITORING"},
        {"action": "DELETE", "object": "MONITORING"},
        {"action": "GET", "object": "RULES"},
        {"action": "GET", "object": "ACTION"},
        {"action": "GET", "object": "ALERT"},
        {"action": "POST", "object": "ALERT"},
        {"action": "PATCH", "object": "ALERT"},
        {"action": "DELETE", "object": "ALERT"},
        {"action": "GET", "object": "NOTIFICATIONS"},
        {"action": "DELETE", "object": "NOTIFICATIONS"},
        {"action": "POST", "object": "NOTIFICATIONS"},
        {"action": "GET", "object": "GROUPS"},
        {"action": "GET", "object": "TASKS"},
    ],
    "ssdrf": [
        {"action": "GET", "object": "ROLES"},
        {"action": "POST", "object": "ROLES"},
        {"action": "PATCH", "object": "ROLES"},
        {"action": "POST", "object": "USERS"},
    ],
}

# logic that implements RBAC.
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
