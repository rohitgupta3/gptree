from contextlib import contextmanager
import os

from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/simple_app"
)

# Fix for PostgreSQL URLs from Heroku
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session
