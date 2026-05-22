import uuid
from datetime import datetime

from pydantic import BaseModel


class InboxItemResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    type: str
    status: str
    title: str
    candidate_count: int
    created_at: datetime
    target_id: uuid.UUID
