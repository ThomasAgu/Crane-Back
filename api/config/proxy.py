''' This module contains the functions to generate the proxy configuration for the Traefik service. '''


def get_config(app_name: str):
    ''' Get proxy config for app '''
    config = {
        "name": "traefik-proxy",
        "image": "traefik:latest",
        "command": [
            "--api.insecure=true",
            "--providers.docker=true",
            "--accesslog=true",
            "--accesslog.format=json",
            "--metrics.prometheus=true",
            "--metrics.prometheus.buckets=0.1,0.3,1.2,5.0",
            "--entrypoints.web.address=:80",
            "--providers.docker.constraints=" +
            "Label(`a.label.name`, `" + app_name + "`)",
            "--providers.docker.watch=true",
        ],
        "ports": ["0:80", "0:8080"],
        "expose": ["8080"],
        "volumes": ["/var/run/docker.sock:/var/run/docker.sock"],
        "networks": ["crane-net", "prometheus-net"],
        "labels": {
            "traefik.enable": "true",
            "traefik.http.routers.traefik.rule": "Host(`traefik." + app_name + ".local`)",
            "traefik.http.routers.traefik.entrypoints": "web",
            "traefik.http.routers.traefik.middlewares": "traefik-auth",
        }
    }

    return config
