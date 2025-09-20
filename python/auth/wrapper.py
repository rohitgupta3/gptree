from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

# Create an instance of HTTPBearer
bearer_scheme = HTTPBearer()


async def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    """
    Dependency to get the current Firebase authenticated user.
    """
    try:
        # Verify the ID token and return the user's claims.
        decoded_token = auth.verify_id_token(token.credentials)
        return decoded_token
    except Exception as e:
        # Raise an HTTPException if the token is invalid or an error occurs.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
