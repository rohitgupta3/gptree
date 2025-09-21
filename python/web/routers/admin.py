# TODO: remove this entire module, this is just for quick iteration early on
from auth.firebase import (
    get_current_user,
)
from database import seed
from database.database import create_all_tables, get_session, get_test_session
from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import auth as fb_auth
from models.user import User
from pydantic import BaseModel
from sqlalchemy import inspect
from sqlmodel import Session, select
from web.schemas.user import CurrentUser

router = APIRouter(prefix="/api", tags=["admin"])


class StatusResponse(BaseModel):
    success: bool
    message: str


class SeedResponse(BaseModel):
    success: bool


def seed_user(session: Session) -> bool:
    """
    Fetch all users from Firebase and sync them to the database.
    Returns True if it succeeded
    """
    # Get all users from Firebase (paginated)
    page = fb_auth.list_users()
    firebase_users = []

    while page:
        firebase_users.extend(page.users)
        page = page.get_next_page() if page.has_next_page else None

    # Process each Firebase user
    for fb_user in firebase_users:
        if not fb_user.email:
            raise ValueError(f"{fb_user} doesn't have an email?")

        # Check if user already exists in DB. TODO: should be `one`?
        existing_user = session.exec(
            select(User).where(User.uid == fb_user.uid)
        ).one_or_none()

        if existing_user:
            pass
        else:
            # Create new user
            new_user = User(uid=fb_user.uid, email=fb_user.email)
            session.add(new_user)

    session.commit()
    return True


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


# TODO: remove this endpoint in production, at least?
@router.post("/reset-test-db", response_model=StatusResponse)
def reset_test_database(session: Session = Depends(get_test_session)):
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


@router.post("/seed-users", response_model=SeedResponse)
def seed_users(session: Session = Depends(get_session)):
    """
    Sync all Firebase users to the database.
    This endpoint can be used to populate the database with existing Firebase users.
    """
    try:
        _ = seed_user(session)
        turn_success = seed.seed_turns(session)

        return SeedResponse(
            success=turn_success,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed users: {e}")
