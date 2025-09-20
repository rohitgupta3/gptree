from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from pydantic import BaseModel
from uuid import UUID

from models.user import User
from web.database import get_session

app = FastAPI(title="Simple User Project API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Default Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response model for user data
class UserDataResponse(BaseModel):
    user_id: str


@app.get("/api/user/{user_id}", response_model=UserDataResponse)
def get_user(user_id: str, session: Session = Depends(get_session)):
    # Validate user_id as UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Get user from the DB
    user = session.get(User, user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserDataResponse(user_id=str(user.id))
