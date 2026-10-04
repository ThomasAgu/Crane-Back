from pydantic import BaseModel

class RepositoryItemCreate(BaseModel):
    name: str
    description: str
    services: str
    app_id: int
    user_id: int
