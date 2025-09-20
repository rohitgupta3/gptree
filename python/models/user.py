import uuid
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func
from sqlalchemy_utils import UUIDType
import sqlalchemy
from models.metadata import MAIN


class User(SQLModel, table=True):
    metadata = MAIN
    __tablename__ = "users"

    id: uuid.UUID = Field(
        sa_column=Column(
            UUIDType,
            primary_key=True,
            server_default=sqlalchemy.sql.text("gen_random_uuid()"),
        ),
        default_factory=uuid.uuid4,
    )

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )

    first_name: str
    last_name: str | None
