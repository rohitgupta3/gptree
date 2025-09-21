import base64
import os
from typing import Any

import firebase_admin
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as fb_auth
from firebase_admin import credentials

# TODO: remove from web
from web.schemas.user import CurrentUser

bearer_scheme = HTTPBearer(auto_error=False)


def authenticate():
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


def verify_firebase_token(token: str) -> dict[str, Any]:
    return fb_auth.verify_id_token(token)


# TODO: try to remove async/await
# TODO: if this is FastAPI-coupled, figure out better organization
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
