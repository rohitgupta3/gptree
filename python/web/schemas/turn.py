from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TurnResponse(BaseModel):
    id: UUID
    parent_id: UUID | None
    primary_child_id: UUID | None
    branched_child_ids: list[UUID]
    human_text: str | None
    bot_text: str | None
    created_at: datetime
