from python.models.user import User


from firebase_admin import auth as fb_auth
from sqlmodel import Session, select


def seed_turns():
    pass


def seed_users_impl(session: Session) -> bool:
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
