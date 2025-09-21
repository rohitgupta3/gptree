# TODO: remove this entire module, this is just for quick iteration early on
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sqlalchemy import inspect
from pydantic import BaseModel

from database.database import create_all_tables, get_session
from python.database.seed import seed_users_impl


router = APIRouter(prefix="/api", tags=["admin"])


class StatusResponse(BaseModel):
    success: bool
    message: str


class SeedUsersResponse(BaseModel):
    success: bool


# TODO: remove this endpoint in production, at least?
@router.post("/reset-db", response_model=StatusResponse)
def reset_database(session: Session = Depends(get_session)):
    bind = session.get_bind()

    try:
        with bind.begin() as conn:
            create_all_tables(conn, drop_first=True)

            inspector = inspect(conn)
            tables = inspector.get_table_names(schema="main")

        return StatusResponse(
            success=True, message=f"Reset successful. Tables now: {tables}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")


@router.post("/seed-users", response_model=SeedUsersResponse)
def seed_users(session: Session = Depends(get_session)):
    """
    Sync all Firebase users to the database.
    This endpoint can be used to populate the database with existing Firebase users.
    """
    try:
        success = seed_users_impl(session)

        return SeedUsersResponse(
            success=success,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed users: {e}")
