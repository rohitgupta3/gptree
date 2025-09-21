import importlib
import os
import pkgutil

from sqlmodel import create_engine, Session, SQLModel

from models.metadata import MAIN

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
