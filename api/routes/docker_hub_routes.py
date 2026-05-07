"""
Routes for Docker Hub image search and details
"""
from fastapi import APIRouter, Query, Path
from typing import List, Dict, Any
from api.services.docker_hub_service import search_docker_images, get_image_details

dockerHubRouter = APIRouter(tags=["docker-hub"])


@dockerHubRouter.get("/search", response_model=List[Dict[str, Any]])
async def search_images(
    query: str 
):
    """
    Search for Docker images on Docker Hub.
    
    Returns a list of matching repositories with basic information.
    """
    return await search_docker_images(query)


@dockerHubRouter.get("/{image_name}/details", response_model=Dict[str, Any])
async def get_image_info(
    image_name: str
):
    """
    Get detailed information about a specific Docker image from Docker Hub.
    
    Returns detailed metadata about the image including description, pull counts, etc.
    """
    print(f"Received request for image details: {image_name}")
    return await get_image_details(image_name)
