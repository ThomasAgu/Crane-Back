''' This file contains the Pydantic models for the User schema. '''

from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    id: Optional[int]
    name: str
    email: str


class UserCount(BaseModel):
    total: int
