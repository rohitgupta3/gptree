from typing import Any

from pydantic import BaseModel


class CurrentUser(BaseModel):
    uid: str
    email: str
    name: str | None = None
    picture: str | None = None
    email_verified: bool | None = None
    claims: dict[str, Any] = {}
