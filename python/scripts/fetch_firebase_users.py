import base64
import os

import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from sqlmodel import Session

from database import engine

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


def print_firebase_users(session: Session) -> tuple[int, int]:
    """
    Fetch all users from Firebase and sync them to the database.
    Returns tuple of (users_added, users_updated)
    """
    breakpoint()
    try:
        # Get all users from Firebase (paginated)
        page = fb_auth.list_users()
        breakpoint()
        firebase_users = []

        while page:
            firebase_users.extend(page.users)
            page = page.get_next_page() if page.has_next_page else None

        # Process each Firebase user
        for fb_user in firebase_users:
            print(fb_user.email)
        #     # Skip users without email (shouldn't happen in most cases)
        #     if not fb_user.email:
        #         continue

        #     # Check if user already exists in DB
        #     existing_user = session.exec(
        #         session.query(User).filter(User.uid == fb_user.uid)
        #     ).first()

        #     if existing_user:
        #         # Update existing user if email changed
        #         if existing_user.email != fb_user.email:
        #             existing_user.email = fb_user.email
        #             session.add(existing_user)
        #             users_updated += 1
        #     else:
        #         # Create new user
        #         new_user = User(uid=fb_user.uid, email=fb_user.email)
        #         session.add(new_user)
        #         users_added += 1

        # session.commit()

    except Exception as e:
        pass
        # session.rollback()
        # raise HTTPException(
        #     status_code=500, detail=f"Failed to sync Firebase users: {str(e)}"
        # )


if __name__ == "__main__":
    with Session(engine) as session:
        print_firebase_users(None)
