from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    picture: str | None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
