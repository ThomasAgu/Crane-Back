## CRANE: despliegue de aplicaciones contenerizadas en entornos locales

CRANE es una herramienta diseñada para el despliegue local de aplicaciones en contenedores, enfocada en simplificar las pruebas de entornos distribuidos de forma local. CRANE ofrece una solución liviana y de propósito general con capacidades de ruteo, escalado y monitoreo automático. Orientada a estudiantes, docentes y
desarrolladores que necesiten crear y desplegar servicios en contenedores simulando las características básicas que ofrece un entorno cloud de plataforma como servicio (PaaS).

### Características
- Desplegar imágenes a través de API REST diseñada con Python Fast API.
- Monitoreo y Alertado automático utilizando Prometheus y AlertManager.
- Evaluación de políticas de seguridad y escalado utilizando Open Policy Agent.
- Modelo RBAC para la autenticación y autorización.
- Documentación con Swagger OPEN API.


## 🔗 Videos demostrativos
[DEMO 1: INICIO DE CRANE](https://drive.google.com/file/d/12CNwgmc6HoB1oHBe1uoRmNLRs5ddVTOT/view?usp=sharing)

[DEMO 2: CREAR SERVICIO](https://drive.google.com/file/d/1nvo89CqVDqeXvcTlSXZMz-S5fEIWKCk4/view?usp=sharing)

[DEMO 3: AUTO START DE SERVICIO CAIDO](https://drive.google.com/file/d/1VmrdGA-yz6MwEoNjJf-bVAl4F5pG8qeE/view?usp=sharing)

[DEMO 4: ESCALAMIENTO AUTOMATICO](https://drive.google.com/file/d/1jVokt9Al6N15-3VulOaImbHSVAw03kRh/view?usp=sharing)

[DEMO 5: DESESCALAMIENTO AUTOMATICO](https://drive.google.com/file/d/1CuHOBBpaTs90n10xcEKRHGu6lekBxtEc/view?usp=sharing)
### Se encuentra a su disposición la colección de Postman en el repositorio


### Requisitos
```
pip install -r requirements.txt
uvicorn main:app --reload
```
#### Importante: El docker daemon debe estar iniciado, de lo contrario recibiremos una advertencia y el servidor no se iniciará.


### Documentación de la API
```http://localhost:8000/docs```


## Arquitectura de ejecución de escenarios

La ejecución de escenarios permite aplicar una condición controlada de caos o
generar carga HTTP sobre una aplicación desplegada. La orquestación comienza en
`scenario_service.py`; este servicio resuelve los registros de la base de datos y
delega el trabajo en `ExecutionManager`, que coordina la resolución de Docker,
el motor de ejecución, la captura de alertas y la generación del resultado.

Los escenarios disponibles se cargan desde `api/files/scenarios.json` a la tabla
de escenarios durante el inicio de la aplicación. Cada registro define una
categoría (`chaos` o `stress`) y un `function_name`, que identifica el método que
ejecutará el motor correspondiente.

### Flujo de una petición

El endpoint `POST /api/v1/scenario/{scenario_id}/app/{app_id}` ejecuta el
siguiente flujo:

```mermaid
sequenceDiagram
        autonumber
        actor Cliente
        participant Ruta as scenario_routes
        participant Servicio as scenario_service
        participant DB as Base de datos
        participant Manager as ExecutionManager
        participant Resolver as DockerResolver
        participant Docker as Docker / Compose
        participant Alertas as AlertCollector
        participant AM as AlertManager
        participant Motor as ChaosEngine o StressEngine
        participant Reporte as ReportGenerator

        Cliente->>Ruta: POST /api/v1/scenario/{scenario_id}/app/{app_id}
        Ruta->>Servicio: manage_scenario(db, scenario_id, app_id)
        Servicio->>DB: Buscar escenario y aplicación
        DB-->>Servicio: Modelos Scenario y App
        Servicio->>Manager: execute(scenario, app)
        Manager->>Resolver: resolve(app_name, project_name)
        Resolver->>Docker: Buscar contenedor activo y obtener red/puertos
        Docker-->>Resolver: Contenedor y datos de conexión
        Resolver-->>Manager: AppContext con nombre, contenedor y URL
        Manager->>Manager: Validar parámetros y categoría
        par Captura durante la ejecución
                Manager->>Alertas: start()
                loop Cada 5 segundos
                        Alertas->>AM: GET /api/v2/alerts (filtro job)
                        AM-->>Alertas: Alertas actuales
                end
        and Aplicar escenario
                alt category = chaos
                        Manager->>Motor: Ejecutar método en el contenedor Docker
                else category = stress
                        Manager->>Motor: Ejecutar método Locust contra service_url
                end
                Motor-->>Manager: Resultado, eventos y métricas
        end
        Manager->>Alertas: stop() y obtener eventos/resumen
        Manager->>Reporte: build(resultado, alertas, metadatos)
        Reporte-->>Manager: ScenarioReport con veredicto
        Manager-->>Servicio: ScenarioReport
        Servicio-->>Ruta: report.to_dict()
        Ruta-->>Cliente: JSON del reporte
```

### Responsabilidades de los componentes

- **`scenario_routes.py`** expone la operación HTTP y delega la ejecución al
    servicio. El prefijo `/api` se configura en `main.py`.
- **`scenario_service.py`** consulta el escenario y la aplicación mediante
    `scenario_crud.get_by_id` y `app_crud.get_by_id`. Devuelve `404` si no existe
    alguno de los dos; si existen, llama al manager y convierte su reporte a un
    diccionario para la respuesta.
- **`ExecutionManager`** normaliza el escenario en `ScenarioParams` y la app en
    `AppContext`, valida los datos y elige el motor por `category`. También
    garantiza que el recolector se detenga con `finally` y coordina la generación
    del reporte.
- **`DockerResolver`** usa el cliente compartido de Docker para localizar un
    contenedor activo del servicio, consultar sus redes y puertos, y construir la
    URL que recibirá el motor de carga. Si no encuentra contenedor devuelve `404`;
    si no puede construir una URL utilizable devuelve `422`.
- **`ChaosEngine`** ejecuta el método indicado por `function_name` dentro del
    contenedor mediante Docker. Sus escenarios aplican fallos de red con `tc`,
    presión de CPU/memoria/disco con `stress-ng` o acciones de ciclo de vida como
    pausar, reiniciar o terminar el contenedor.
- **`StressEngine`** ejecuta escenarios de Locust contra la URL resuelta, por
    ejemplo carga lineal, tráfico en pico o carga sostenida. Locust corre en un
    thread executor para no bloquear el event loop de FastAPI y produce métricas
    como solicitudes, tasa de error y latencias.
- **`AlertCollector`** consulta AlertManager en segundo plano cada cinco segundos
    mientras corre el motor. Registra eventos de alerta y evita repetir la misma
    huella en el mismo estado. Un fallo de conexión se registra y no detiene el
    bucle de captura.
- **`ReportGenerator`** combina metadatos, resultado del motor, métricas de carga
    (si el escenario es `stress`) y alertas. Calcula `PASSED`, `DEGRADED` o
    `FAILED` según el éxito del motor, los umbrales de rendimiento y las alertas
    activas. Finalmente, `ScenarioReport.to_dict()` forma el JSON de respuesta.

El reporte de ejecución se genera al terminar cada petición y se devuelve al
cliente; esta ruta no lo guarda como historial en la base de datos. Es distinto
del sistema de reportes históricos documentado en `REPORT_SYSTEM.md`.


### Endpoint de Prometheus:
```http://localhost:9090```


### Endpoint de AlertManager:
```http://localhost:9093```


### Registro
```
curl --location 'http://localhost:8000/api/v1/auth/register' \
--header 'Content-Type: application/json' \
--data-raw '{
    "full_name": "Franco Bellino",
    "email": "franco@gmail.com",
    "password": "123456"
}'
```


### Login
```
curl --location 'http://localhost:8000/api/v1/auth/login' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "franco@gmail.com",
    "password": "123456"
}'
```


### Desplegar mi primer servicio


```
curl --location 'http://localhost:8000/api/v1/apps' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImZyYW5jb0BnbWFpbC5jb20iLCJyb2xlcyI6WyJBRE1JTiJdfQ.QkZ8W1uxFQ9CWIgo1YFCJaOC-2-2C7J4zrPSsZhVfBM' \
--data '{
    "name": "prueba_demo_crane",
    "services": [
        {
            "name": "whoami",
            "image": "traefik/whoami",
            "networks": [
                "crane-net"
            ]
        }
    ]
}'
```
