import os
from typing import Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from pydantic import BaseModel
from uuid import UUID

from auth.firebase import (
    verify_firebase_token,
    authenticate as authenticate_to_firebase,
)
from models.user import User
from models.turn import Turn
from database import get_session
from web.routers import admin


authenticate_to_firebase()

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


class CreateConversationRequest(BaseModel):
    text: str


class CreateConversationResponse(BaseModel):
    turn_id: UUID


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        decoded = verify_firebase_token(creds.credentials)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase ID token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

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


def _stub_gemini(session: Session, turn_id: UUID) -> None:
    """
    Stub function for Gemini API interaction.
    In the real implementation, this would call the actual Gemini API.
    """
    # Get the turn to access the human text
    turn = session.get(Turn, turn_id)
    if not turn:
        raise ValueError(f"Turn {turn_id} not found")

    # Generate a simple response based on the human input
    bot_response = f"I see that you said {turn.human_text}"

    # Update the turn with the bot response
    turn.bot_text = bot_response
    session.add(turn)
    session.commit()


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


@app.get("/.health")
def get_status():
    return JSONResponse(content={"success": True})


@app.get("/api/me", response_model=CurrentUser)
async def read_me(user: CurrentUser = Depends(get_current_user)):
    return user


@app.post("/api/user", response_model=UserDataResponse)
def create_user(payload: CreateUserRequest, session: Session = Depends(get_session)):
    user = User(uid=payload.uid, email=payload.email)
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserDataResponse(user_id=str(user.id))


@app.post("/api/conversation/create", response_model=CreateConversationResponse)
async def create_conversation(
    payload: CreateConversationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Create a new conversation by creating the initial turn and generating a response
    """
    # First, get the User record from the database using the Firebase UID
    user = session.exec(select(User).where(User.uid == current_user.uid)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in database")

    # Create a new Turn with the user's input
    turn = Turn(
        user_id=user.id,
        human_text=payload.text,
        parent_turn_id=None,  # This is the root turn of a new conversation
        model="gemini-2.5-flash",
        bot_text=None,  # Will be filled by the stub function
    )

    session.add(turn)
    session.commit()
    session.refresh(turn)

    # Get the turn ID before calling the stub
    turn_id = turn.id

    try:
        # Call the Gemini stub to generate a response
        # TODO: explore removing async/await here
        _stub_gemini(session, turn_id)
    except Exception as e:
        # If the stub fails, we should still return the turn ID
        # but log the error for debugging
        print(f"Error calling Gemini stub: {e}")

    return CreateConversationResponse(turn_id=turn_id)


app.include_router(admin.router)


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
