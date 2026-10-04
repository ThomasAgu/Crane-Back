package rbac.authz

import rego.v1

role_permissions := {
    "ADMIN": [
        {"action": "GET", "object": "USERS", "description": "Ver los usuarios del sistema"},
        {"action": "POST", "object": "USERS", "description": "Modificar los usuarios del sistema"},
        {"action": "GET",  "object": "ROLES", "description": "Ver los roles del sistema"},
        {"action": "POST",  "object": "ROLES", "description": "Crear roles en el sistema"},
        {"action": "PATCH",  "object": "ROLES", "description": "Actualizar los roles del sistema"},
        {"action": "DELETE",  "object": "ROLES", "description": "Eliminar los roles creados por usuarios"},
        {"action": "GET", "object": "PERMISSIONS", "description": "Consultar la lista de permisos del sistema"},
        {"action": "POST", "object": "PERMISSIONS", "description": "Crear o asignar nuevos permisos"},
        {"action": "GET", "object": "REPOSITORYMODERATOR", "description": "Consultar opciones y herramientas de moderación del repositorio"},
        {"action": "GET", "object": "GROUPS", "description": "Consultar grupos de estudiantes o cursos"},
        {"action": "DELETE", "object": "GROUPS", "description": "Eliminar grupos de trabajo creados"},
        {"action": "POST", "object": "GROUPS", "description": "Crear nuevos grupos de trabajo para estudiantes"},
        {"action": "GET", "object": "TASKS", "description": "Consultar tareas asignadas a los alumnos"},
        {"action": "DELETE", "object": "TASKS", "description": "Eliminar tareas creadas"},
        {"action": "POST", "object": "TASKS", "description": "Crear y publicar tareas para los estudiantes"},
    ],
    "OPERATOR": [
        {"action": "GET", "object": "REPOSITORYMODERATOR", "description": "Consultar opciones y herramientas de moderación del repositorio"},
    ],
    "PROFESSOR": [
        {"action": "GET", "object": "GROUPS", "description": "Consultar grupos de estudiantes o cursos"},
        {"action": "GET", "object": "USERS", "description": "Ver los usuarios del sistema"},
        {"action": "DELETE", "object": "GROUPS", "description": "Eliminar grupos de trabajo creados"},
        {"action": "POST", "object": "GROUPS", "description": "Crear nuevos grupos de trabajo para estudiantes"},
        {"action": "GET", "object": "TASKS", "description": "Consultar tareas asignadas a los alumnos"},
        {"action": "DELETE", "object": "TASKS", "description": "Eliminar tareas creadas"},
        {"action": "POST", "object": "TASKS", "description": "Crear y publicar tareas para los estudiantes"},
    ],
    "USER": [
        {"action": "GET", "object": "APPS", "description": "Consultar o listar aplicaciones disponibles"},
        {"action": "POST", "object": "APPS", "description": "Crear o registrar una nueva aplicación propia"},
        {"action": "PATCH", "object": "APPS", "description": "Actualizar parcialmente datos de aplicaciones propias"},
        {"action": "DELETE", "object": "APPS", "description": "Eliminar aplicaciones propias"},
        {"action": "GET", "object": "ROLES", "description": "Consultar información básica sobre los roles disponibles"},
        {"action": "GET", "object": "REPOSITORY", "description": "Consultar o explorar archivos en el repositorio"},
        {"action": "POST", "object": "REPOSITORY", "description": "Subir o publicar nuevos archivos al repositorio"},
        {"action": "PATCH", "object": "REPOSITORY", "description": "Modificar o actualizar archivos propios en el repositorio"},
        {"action": "GET", "object": "OPA", "description": "Consultar políticas de evaluación u OPA aplicables"},
        {"action": "POST", "object": "OPA", "description": "Enviar datos para verificación de políticas en OPA"},
        {"action": "PATCH", "object": "OPA", "description": "Modificar entradas/datos de evaluación en OPA"},
        {"action": "DELETE", "object": "OPA", "description": "Eliminar peticiones o datos en OPA"},
        {"action": "GET", "object": "MONITORING", "description": "Ver el avance y monitoreo de sus propias actividades"},
        {"action": "POST", "object": "MONITORING", "description": "Enviar eventos o reportes de estado de sus prácticas"},
        {"action": "PATCH", "object": "MONITORING", "description": "Actualizar estado de monitoreo personal"},
        {"action": "DELETE", "object": "MONITORING", "description": "Eliminar registros personales de monitoreo"},
        {"action": "GET", "object": "RULES", "description": "Consultar reglas de evaluación y entregas"},
        {"action": "GET", "object": "ACTION", "description": "Consultar el historial de acciones realizadas"},
        {"action": "GET", "object": "ALERT", "description": "Ver alertas recibidas sobre fechas limite o tareas"},
        {"action": "POST", "object": "ALERT", "description": "Generar avisos o alertas dirigidas a profesores/tutores"},
        {"action": "PATCH", "object": "ALERT", "description": "Actualizar o dar por atendida una alerta personal"},
        {"action": "DELETE", "object": "ALERT", "description": "Eliminar alertas personales resueltas"},
        {"action": "GET", "object": "NOTIFICATIONS", "description": "Ver notificaciones enviadas por la plataforma o profesores"},
        {"action": "DELETE", "object": "NOTIFICATIONS", "description": "Eliminar notificaciones recibidas"},
        {"action": "POST", "object": "NOTIFICATIONS", "description": "Responder o enviar notificaciones a compañeros o profesores"},
        {"action": "GET", "object": "GROUPS", "description": "Consultar los grupos de trabajo a los que pertenece"},
        {"action": "GET", "object": "TASKS", "description": "Consultar la lista de tareas pendientes o entregadas"},
    ],
}

# logic that implements RBAC.
default allow := false
allow if {
    # 1. Obtenemos el rol del input
    some r in input.roles
    
    # 2. Obtenemos el array de permisos de ese rol de forma segura
    permissions := role_permissions[r]
    
    # 3. Buscamos si el permiso solicitado está dentro de ese array
    some p in permissions
    p.action == input.action
    p.object == input.object
}