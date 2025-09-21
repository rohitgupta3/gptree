from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Column
import sqlalchemy
from sqlalchemy import DateTime, func
from sqlalchemy.dialects import postgresql
import sqlalchemy_utils
from sqlalchemy_utils import UUIDType

from models.metadata import MAIN


class Turn(SQLModel, table=True):
    metadata = MAIN
    __tablename__ = "turn"

    id: UUID = Field(
        sa_column=Column(
            UUIDType,
            primary_key=True,
            server_default=sqlalchemy.sql.text("gen_random_uuid()"),
        ),
        default_factory=uuid4,
    )

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )

    parent_id: UUID | None
    # children_turn_ids: list[UUID]
    primary_child_id: UUID | None
    branched_child_ids: list[UUID] = Field(
        sa_type=postgresql.ARRAY(sqlalchemy_utils.UUIDType),
        default_factory=list,
    )
    user_id: UUID
    human_text: str
    model: str
    # TODO: other human input e.g. files, model, mode, style, etc
    # TODO: maybe put some validation on below being non-null once the LLM has returned
    bot_text: str | None
    # TODO: other bot input
    # TODO: llm_request_id once that is set up
