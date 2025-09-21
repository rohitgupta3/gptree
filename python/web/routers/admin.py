# TODO: remove this entire module, this is just for quick iteration early on
import importlib
import pkgutil

from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import auth as fb_auth
from sqlmodel import Session, select
from sqlalchemy import inspect
from pydantic import BaseModel

from models.metadata import MAIN
from models.user import User
from database import get_session


router = APIRouter(prefix="/api", tags=["admin"])


class StatusResponse(BaseModel):
    success: bool
    message: str


class SeedUsersResponse(BaseModel):
    success: bool


def import_modules(package, recursive=True):
    """
    Import all submodules of a module, recursively, including subpackages.
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    for _, name, is_pkg in pkgutil.walk_packages(package.__path__):
        if "." in name:
            continue
        full_name = package.__name__ + "." + name
        importlib.import_module(full_name)
        if recursive and is_pkg:
            import_modules(full_name)


# Import all models recursively under python/models, this allows the DB reset to work
import_modules("models")


# def sync_firebase_users_to_db(session: Session) -> tuple[int, int]:
#     """
#     Fetch all users from Firebase and sync them to the database.
#     Returns tuple of (users_added, users_updated)
#     """
#     users_added = 0
#     users_updated = 0

#     try:
#         # Get all users from Firebase (paginated)
#         page = fb_auth.list_users()
#         firebase_users = []

#         while page:
#             firebase_users.extend(page.users)
#             page = page.get_next_page() if page.has_next_page else None

#         # Process each Firebase user
#         for fb_user in firebase_users:
#             # Skip users without email (shouldn't happen in most cases)
#             if not fb_user.email:
#                 continue

#             # Check if user already exists in DB
#             existing_user = session.exec(
#                 session.query(User).filter(User.uid == fb_user.uid)
#             ).first()

#             if existing_user:
#                 # Update existing user if email changed
#                 if existing_user.email != fb_user.email:
#                     existing_user.email = fb_user.email
#                     session.add(existing_user)
#                     users_updated += 1
#             else:
#                 # Create new user
#                 new_user = User(uid=fb_user.uid, email=fb_user.email)
#                 session.add(new_user)
#                 users_added += 1

#         session.commit()

#     except Exception as e:
#         session.rollback()
#         raise HTTPException(
#             status_code=500, detail=f"Failed to sync Firebase users: {str(e)}"
#         )


#     return users_added, users_updated


def seed_user(session: Session) -> bool:
    """
    Fetch all users from Firebase and sync them to the database.
    Returns True if it succeeded
    """
    try:
        # Get all users from Firebase (paginated)
        page = fb_auth.list_users()
        firebase_users = []

        while page:
            firebase_users.extend(page.users)
            page = page.get_next_page() if page.has_next_page else None

        # Process each Firebase user
        for fb_user in firebase_users:
            print(fb_user.email)
            if not fb_user.email:
                raise ValueError(f"{fb_user} doesn't have an email?")

            # Check if user already exists in DB. TODO: should be `one`?
            existing_user = session.exec(
                select(User).where(User.uid == fb_user.uid)
            ).one_or_none()

            if existing_user:
                print(f"Already have user with uid {fb_user.uid}")
            else:
                # Create new user
                new_user = User(uid=fb_user.uid, email=fb_user.email)
                session.add(new_user)

        session.commit()
        return True

    except Exception as e:
        print(f"Exception hit, rolling back: {e}")
        session.rollback()
        return False


# TODO: remove this endpoint in production, at least?
@router.post("/reset-db", response_model=StatusResponse)
def reset_database(session: Session = Depends(get_session)):
    bind = session.get_bind()

    try:
        with bind.begin() as conn:
            MAIN.drop_all(bind=conn)
            MAIN.create_all(bind=conn)

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
        success = seed_user(session)

        return SeedUsersResponse(
            success=success,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed users: {e}")
