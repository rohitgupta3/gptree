import base64
import importlib
import os
import pkgutil
from typing import Any

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect
from sqlmodel import Session, select, SQLModel
from pydantic import BaseModel
from uuid import UUID
import firebase_admin
from firebase_admin import auth as fb_auth, credentials


from models.metadata import MAIN  # This is your MetaData(schema="main")
from models.user import User
from web.database import get_session

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


bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    uid: str
    email: str
    name: str | None = None
    picture: str | None = None
    email_verified: bool | None = None
    claims: dict[str, Any] = {}


class CreateUserRequest(BaseModel):
    uid: str
    email: str


def verify_firebase_token(token: str) -> dict[str, Any]:
    try:
        return fb_auth.verify_id_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase ID token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    decoded = verify_firebase_token(creds.credentials)
    reserved = {
        "aud",
        "auth_time",
        "exp",
        "firebase",
        "iat",
        "iss",
        "sub",
        "uid",
        "user_id",
        "email",
        "email_verified",
        "name",
        "picture",
    }
    custom_claims = {k: v for k, v in decoded.items() if k not in reserved}

    return CurrentUser(
        uid=decoded.get("uid") or decoded.get("user_id"),
        email=decoded.get("email"),
        name=decoded.get("name"),
        picture=decoded.get("picture"),
        email_verified=decoded.get("email_verified"),
        claims=custom_claims,
    )


app = FastAPI(title="Simple User Project API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "https://gptree-62f38493fe71.herokuapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class UserDataResponse(BaseModel):
    user_id: str


class StatusResponse(BaseModel):
    success: bool
    message: str


## TODO: remove this, this is so maybe we get access to all the models for resetting the DB
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


# Import all models recrusively under python/models
import_modules("models")


# TODO: remove this
@app.post("/api/reset-db", response_model=StatusResponse)
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


@app.get("/status")
def get_status():
    return JSONResponse(content={"success": True})


@app.get("/api/test", response_model=StatusResponse)
def test_connection():
    """Simple test endpoint to verify frontend-backend communication"""
    return StatusResponse(success=True, message="Backend is working correctly!")


@app.get("/api/me", response_model=CurrentUser)
async def read_me(user: CurrentUser = Depends(get_current_user)):
    print(user)
    return user


@app.get("/api/user", response_model=UserDataResponse)
# def get_current_user(session: Session = Depends(get_session)):
def get_current_user(request: Request, session: Session = Depends(get_session)):
    user = session.scalars(select(User)).one()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserDataResponse(user_id=str(user.id))


@app.get("/api/user/{user_id}", response_model=UserDataResponse)
def get_user(user_id: str, session: Session = Depends(get_session)):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = session.get(User, user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserDataResponse(user_id=str(user.id))


@app.post("/api/user", response_model=UserDataResponse)
def create_user(payload: CreateUserRequest, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.uid == payload.uid)).first()
    if existing_user:
        return UserDataResponse(user_id=str(existing_user.id))

    user = User(uid=payload.uid, email=payload.email)
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserDataResponse(user_id=str(user.id))


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    """Serve the frontend SPA for all routes that don't match API endpoints"""

    # Don't serve SPA for API routes or static files
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not found")

    # Check if static directory exists
    if not os.path.exists(static_dir):
        raise HTTPException(status_code=404, detail="Frontend not built")

    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Frontend not built")
