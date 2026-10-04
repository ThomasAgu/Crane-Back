''' This file contains the schema for the role model. '''
from typing import Optional
from pydantic import BaseModel


class Role(BaseModel):
    id: Optional[int]
    name: str
