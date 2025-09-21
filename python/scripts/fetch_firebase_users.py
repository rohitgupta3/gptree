import base64
import os

import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from sqlmodel import Session, select

from database import engine
from models.user import User

# TODO: extract Firebase auth

project_id = os.getenv("FIREBASE_PROJECT_ID")
client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
private_key_b64 = os.getenv("FIREBASE_PRIVATE_KEY_BASE64")

if not project_id or not client_email or not private_key_b64:
    raise RuntimeError("Missing required Firebase environment variables")

# Decode the base64 private key
private_key = base64.b64decode(private_key_b64).decode("utf-8")

if not firebase_admin._apps:
    cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": project_id,
            "private_key_id": "dummy",  # not strictly used in verification
            "private_key": private_key,
            "client_email": client_email,
            "client_id": "dummy",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email}",
        }
    )
    firebase_admin.initialize_app(cred)


# TODO: if this works well in the web app, remove from here
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


if __name__ == "__main__":
    with Session(engine) as session:
        seed_user(session)
