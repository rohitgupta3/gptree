import datetime
import logging
import os
from uuid import UUID

from auth.firebase import (
    authenticate as authenticate_to_firebase,
)
from auth.firebase import get_current_user
from database.database import get_session
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from llm.llm import gemini_with_fallback
from models.turn import Turn
from models.user import User
from pydantic import BaseModel
from sqlmodel import Session, select
from web.dao import conversations
from web.dao.conversations import get_full_conversation_from_turn_id, reply_to_turn
from web.routers import admin
from web.schemas.turn import TurnResponse
from web.schemas.user import CurrentUser

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

authenticate_to_firebase()


# TODO: move these into schemas
class CreateUserRequest(BaseModel):
    uid: str
    email: str


class CreateConversationRequest(BaseModel):
    text: str


class CreateConversationResponse(BaseModel):
    turn_id: UUID


class UserDataResponse(BaseModel):
    user_id: str


class ConversationListItem(BaseModel):
    root_turn_id: UUID
    identifying_turn_id: UUID
    title: str
    created_at: datetime.datetime


class ReplyRequest(BaseModel):
    parent_turn_id: UUID
    text: str


class BranchReplyRequest(BaseModel):
    parent_turn_id: UUID
    text: str


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
        parent_id=None,  # This is the root turn of a new conversation
        title=f"{payload.text[:20]}",  # TODO: fix
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
        gemini_with_fallback(session, turn_id, create_title=True)
    except Exception as e:
        # If the stub fails, we should still return the turn ID
        # but log the error for debugging
        logger.error(f"Error calling Gemini stub: {e}")

    return CreateConversationResponse(turn_id=turn_id)


@app.get("/api/conversations", response_model=list[ConversationListItem])
def list_conversations(
    current_user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.uid == current_user.uid)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    turns = conversations.get_separable_conversations(session, user.id)

    return [
        ConversationListItem(
            root_turn_id=t.id,  # TODO: this is wrong
            identifying_turn_id=t.id,  # or another ID if you track branches separately
            title=t.title,
            created_at=t.created_at,
        )
        for t in turns
    ]


@app.get("/api/conversation/{turn_id}", response_model=list[TurnResponse])
def get_conversation_by_turn_id(
    turn_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.uid == current_user.uid)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    full_convo = get_full_conversation_from_turn_id(session, turn_id, user.id)

    if not full_convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return full_convo


@app.post("/api/conversation/reply", response_model=TurnResponse)
def reply_to_conversation(
    payload: ReplyRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.uid == current_user.uid)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_turn = reply_to_turn(
        session=session,
        user_id=user.id,
        parent_turn_id=payload.parent_turn_id,
        text=payload.text,
    )

    # Optional: call Gemini stub to populate bot_text
    try:
        gemini_with_fallback(session, new_turn.id)
    except Exception as e:
        logger.error(f"Stub failed: {e}")

    return new_turn


@app.post("/api/conversation/branch-reply", response_model=TurnResponse)
def branch_reply_to_conversation(
    payload: BranchReplyRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.uid == current_user.uid)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_turn = conversations.branch_reply_to_turn(
        session=session,
        user_id=user.id,
        parent_turn_id=payload.parent_turn_id,
        text=payload.text,
    )

    try:
        gemini_with_fallback(session, new_turn.id, create_title=True)
    except Exception as e:
        logger.error(f"Branch stub failed: {e}")

    return new_turn


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
