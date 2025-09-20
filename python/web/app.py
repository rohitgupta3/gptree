import os

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from pydantic import BaseModel
from uuid import UUID

from models.user import User
from web.database import get_session


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


@app.get("/status")
def get_status():
    return JSONResponse(content={"success": True})


@app.get("/api/test", response_model=StatusResponse)
def test_connection():
    """Simple test endpoint to verify frontend-backend communication"""
    return StatusResponse(success=True, message="Backend is working correctly!")


# TODO: get rid of this
# @app.get("/api/user/random", response_model=UserDataResponse)
# def get_random_user(session: Session = Depends(get_session)):
#     user = session.scalars(select(User)).one()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     return UserDataResponse(user_id=str(user.id))


@app.get("/api/user", response_model=UserDataResponse)
# def get_current_user(session: Session = Depends(get_session)):
def get_current_user(request: Request, session: Session = Depends(get_session)):
    print("---- HEADERS ----")
    for key, value in request.headers.items():
        print(f"{key}: {value}")
    print("-----------------")

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
