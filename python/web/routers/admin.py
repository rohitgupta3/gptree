# TODO: remove this entire module, this is just for quick iteration early on
import importlib
import pkgutil

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sqlalchemy import inspect
from pydantic import BaseModel

from models.metadata import MAIN
from database import get_session


router = APIRouter(prefix="/api", tags=["admin"])


class StatusResponse(BaseModel):
    success: bool
    message: str


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
