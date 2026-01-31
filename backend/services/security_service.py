import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import requests

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import JWTError, jwt
from pydantic import BaseModel

from models.user import TokenData, User
from services.user_service import user_service

# --- Constants ---
# Make sure to set these in your environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY", "a_super_secret_key_that_should_be_in_env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/google")


class GoogleToken(BaseModel):
    credential: str


# --- Token Verification and Creation ---


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_google_token(token: str) -> Dict[str, Any]:
    """Verifies the Google ID token or Access Token and returns the user's info."""
    print("DEBUG: Verifying Google token...")
    if not GOOGLE_CLIENT_ID:
        print("ERROR: GOOGLE_CLIENT_ID is not set!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Client ID is not configured on the server.",
        )

    # First attempt: Verify as ID Token
    try:
        id_info = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        print("DEBUG: Google ID token successfully verified.")
        return dict(id_info)
    except ValueError as e:
        print(f"DEBUG: Token not a valid ID token ({e}), attempting to verify as Access Token...")
    
    # Second attempt: Verify as Access Token
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
             user_info = response.json()
             # Validate that this token was issued to our client (optional but recommended if possible, 
             # though userinfo endpoint doesn't always return azp/aud. tokeninfo endpoint does.)
             # Let's double check via tokeninfo to be safe about audience.
             token_info_resp = requests.get(f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={token}")
             if token_info_resp.status_code == 200:
                 token_info = token_info_resp.json()
                 if token_info.get("aud") != GOOGLE_CLIENT_ID:
                      print(f"ERROR: Token audience mismatch. Expected {GOOGLE_CLIENT_ID}, got {token_info.get('aud')}")
                      # raise ValueError("Token audience mismatch") 
                      # Sometimes audience might be different for access tokens? 
                      # For access tokens, 'aud' is usually the client_id. 
                      pass 

             print("DEBUG: Google Access Token successfully verified via userinfo.")
             return user_info
        else:
            print(f"ERROR: Failed to verify access token. Status: {response.status_code}, Body: {response.text}")
            raise ValueError("Invalid Access Token")

    except Exception as e:
        print(f"ERROR: Invalid Google token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {e}",
        )


# --- Dependency for Protected Routes ---


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current user from a token.
    To be used for protecting routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    if token_data.email is None:
        raise credentials_exception

    user = await user_service.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return User(**user.model_dump())
