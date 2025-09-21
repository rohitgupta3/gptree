import importlib
import os
import pkgutil

from models.metadata import MAIN
from sqlmodel import Session, create_engine

DATABASE_URL = os.environ["DATABASE_URL"]

# Fix for PostgreSQL URLs from Heroku
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]
# Fix for PostgreSQL URLs from Heroku
if TEST_DATABASE_URL.startswith("postgres://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgres://", "postgresql://", 1)

test_engine = create_engine(TEST_DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session


def get_test_session():
    with Session(test_engine) as session:
        yield session


def create_all_tables(bind, *, drop_first=False):
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

    # Create the database schema once when the module is imported
    import_modules("models")
    if drop_first:
        MAIN.drop_all(bind=bind)
    MAIN.create_all(bind=bind)
