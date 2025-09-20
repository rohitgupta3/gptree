from contextlib import contextmanager
import os

from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/simple_app"
)

engine = create_engine(DATABASE_URL)


# # Create all tables
# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)


# Session factory
def get_session():
    with Session(engine) as session:
        yield session


# @contextmanager
# def get_session_context():
#     with Session(engine) as session:
#         yield session
