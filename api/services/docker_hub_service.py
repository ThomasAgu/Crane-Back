"""
Service for handling Docker Hub API interactions (httpx version)
"""
import logging
import httpx
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "MyApp/1.0 (+https://example.com)"
}
TIMEOUT = 10.0


async def search_docker_images(query: str) -> List[Dict[str, Any]]:
    """
    Search for Docker images on Docker Hub.
    """
    if not query or not query.strip():
        return []

    url = f"https://hub.docker.com/v2/search/repositories/?query={query}"

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
            response = await client.get(url)

            if response.status_code != 200:
                logger.error(
                    f"Docker Hub API error {response.status_code}: {response.text}"
                )
                return []

            data = response.json()

            return [
                {
                    "name": item.get("repo_name"),
                    "description": item.get("short_description", ""),
                    "official": item.get("is_official", False),
                    "pulls": item.get("pull_count", 0),
                    "stars": item.get("star_count", 0),
                }
                for item in data.get("results", [])
            ]

    except httpx.TimeoutException:
        logger.error(f"Docker Hub API timeout while searching: {query}")
        return []
    except Exception as e:
        logger.error(f"Error searching Docker images: {str(e)}")
        return []


async def get_image_details(image_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Docker image.
    """
    if not image_name:
        return {}

    url = f"https://hub.docker.com/v2/repositories/{image_name}"

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
            response = await client.get(url)

            if response.status_code != 200:
                logger.error(
                    f"Docker Hub API error {response.status_code}: {response.text}"
                )
                return {}

            data = response.json()

            return {
                "name": data.get("name"),
                "namespace": data.get("namespace"),
                "description": data.get("description", ""),
                "full_description": data.get("full_description", ""),
                "is_official": data.get("is_official", False),
                "pull_count": data.get("pull_count", 0),
                "star_count": data.get("star_count", 0),
                "last_updated": data.get("last_updated"),
            }

    except httpx.TimeoutException:
        logger.error(f"Docker Hub API timeout for {image_name}")
        return {}
    except Exception as e:
        logger.error(f"Error getting details for {image_name}: {str(e)}")
        return {}